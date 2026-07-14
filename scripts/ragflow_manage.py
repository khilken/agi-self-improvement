#!/usr/bin/env python3
"""Hermes manager for RAGFlow.

RAGFlow is a large Docker/Python/Go/Node RAG platform. Hermes keeps it as a
pinned external source tree and manages it through Docker Compose/HTTP/process
boundaries instead of importing its dependencies into the Hermes runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "https://github.com/infiniflow/ragflow.git"
PINNED_COMMIT = "b0cac0ac9dc88dddfde183f62a7d940af07dc9cd"
SOURCE_DIR = Path(os.environ.get("RAGFLOW_SOURCE_DIR", ROOT / "integrations" / "ragflow")).resolve()
HOME = Path(os.environ.get("HERMES_RAGFLOW_HOME", Path.home() / ".hermes" / "ragflow")).resolve()
RUNTIME_DOCKER_DIR = Path(os.environ.get("HERMES_RAGFLOW_DOCKER_DIR", HOME / "docker")).resolve()
COMPOSE_FILE = RUNTIME_DOCKER_DIR / "docker-compose.yml"
BASE_COMPOSE_FILE = RUNTIME_DOCKER_DIR / "docker-compose-base.yml"
ENV_FILE = RUNTIME_DOCKER_DIR / ".env"
WEB_URL = os.environ.get("RAGFLOW_WEB_URL", "http://127.0.0.1:8088").rstrip("/")
API_URL = os.environ.get("RAGFLOW_API_URL", "http://127.0.0.1:9380").rstrip("/")
ADMIN_URL = os.environ.get("RAGFLOW_ADMIN_URL", "http://127.0.0.1:9381").rstrip("/")
MCP_URL = os.environ.get("RAGFLOW_MCP_URL", "http://127.0.0.1:9382").rstrip("/")

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "uv.lock",
    "go.mod",
    "Dockerfile",
    "docker/docker-compose.yml",
    "docker/docker-compose-base.yml",
    "docker/service_conf.yaml.template",
    "docker/entrypoint.sh",
    "docker/init.sql",
    "docker/.env",
    "web/package.json",
]

SENSITIVE_KEY_FRAGMENTS = (
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "API_KEY",
    "PRIVATE",
    "ACCESS_KEY",
)

SAFE_ENV_OVERRIDES = {
    # Use a small local footprint and non-conflicting ports by default.
    "COMPOSE_PROFILES": "cpu,elasticsearch",
    "DEVICE": "cpu",
    "SVR_WEB_HTTP_PORT": "8088",
    "SVR_WEB_HTTPS_PORT": "8443",
    "SVR_HTTP_PORT": "9380",
    "ADMIN_SVR_HTTP_PORT": "9381",
    "SVR_MCP_PORT": "9382",
    "GO_HTTP_PORT": "9384",
    "GO_ADMIN_PORT": "9383",
    "ES_PORT": "9208",
    "EXPOSE_MYSQL_PORT": "3308",
    "MINIO_PORT": "9008",
    "MINIO_CONSOLE_PORT": "9009",
    "REDIS_PORT": "6388",
    "INFINITY_HTTP_PORT": "23828",
    "INFINITY_THRIFT_PORT": "23818",
    "INFINITY_PSQL_PORT": "5438",
    "NATS_PORT": "4228",
    "KIBANA_PORT": "5608",
    "MEM_LIMIT": "8073741824",
    # Local dev credentials only. Override via environment for real deployments.
    "MYSQL_PASSWORD": "hermes-ragflow-mysql-password",
    "ELASTIC_PASSWORD": "hermes-ragflow-elastic-password",
    "OPENSEARCH_PASSWORD": "hermes-ragflow-opensearch-password",
    "MINIO_PASSWORD": "hermes-ragflow-minio-password",
    "REDIS_PASSWORD": "hermes-ragflow-redis-password",
    "OCEANBASE_PASSWORD": "hermes-ragflow-oceanbase-password",
    "OB_SYS_PASSWORD": "hermes-ragflow-ob-sys-password",
    "OB_TENANT_PASSWORD": "hermes-ragflow-ob-tenant-password",
    "SEEKDB_PASSWORD": "hermes-ragflow-seekdb-password",
}


def _run_capture(cmd: list[str], cwd: Path | None = None, timeout: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "cmd": cmd,
        }
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc), "cmd": cmd}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"Timed out after {timeout}s",
            "cmd": cmd,
        }


def _git(args: list[str], timeout: int = 30) -> dict[str, Any]:
    if not SOURCE_DIR.exists():
        return {"ok": False, "stdout": "", "stderr": f"missing source: {SOURCE_DIR}"}
    return _run_capture(["git", *args], cwd=SOURCE_DIR, timeout=timeout)


def _tool_version(cmd: list[str]) -> str | None:
    result = _run_capture(cmd, timeout=10)
    return result["stdout"] if result.get("ok") else None


def _http_probe(url: str, timeout: int = 3) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(300).decode("utf-8", errors="replace")
            return {"ok": 200 <= response.status < 400, "status": response.status, "url": url, "body_preview": body}
    except Exception as exc:
        return {"ok": False, "status": None, "url": url, "error": str(exc)}


def _parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(errors="replace").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_key_summary(path: Path) -> dict[str, Any]:
    values = _parse_env(path)
    return {
        "key_count": len(values),
        "keys": sorted(values),
        "sensitive_keys": sorted(k for k in values if any(fragment in k.upper() for fragment in SENSITIVE_KEY_FRAGMENTS)),
    }


def _write_env_from_template(template: Path, dest: Path) -> None:
    overrides = {**SAFE_ENV_OVERRIDES}
    # Environment variables always win for real local deployments.
    for key in list(overrides):
        if key in os.environ:
            overrides[key] = os.environ[key]
    lines: list[str] = []
    seen: set[str] = set()
    for raw in template.read_text(errors="replace").splitlines():
        if raw.strip() and not raw.lstrip().startswith("#") and "=" in raw:
            key, _value = raw.split("=", 1)
            key = key.strip()
            if key in overrides:
                lines.append(f"{key}={overrides[key]}")
            else:
                lines.append(raw)
            seen.add(key)
        else:
            lines.append(raw)
    for key, value in overrides.items():
        if key not in seen:
            lines.append(f"{key}={value}")
    dest.write_text("\n".join(lines) + "\n")


def status() -> dict[str, Any]:
    commit = _git(["rev-parse", "HEAD"]).get("stdout", "") if SOURCE_DIR.exists() else ""
    branch = _git(["branch", "--show-current"]).get("stdout", "") if SOURCE_DIR.exists() else ""
    missing_files = [rel for rel in REQUIRED_FILES if not (SOURCE_DIR / rel).exists()]
    web_health = _http_probe(WEB_URL, timeout=2)
    api_health = _http_probe(f"{API_URL}/v1/system/version", timeout=2)
    source_ready = SOURCE_DIR.exists() and commit == PINNED_COMMIT and not missing_files
    return {
        "ok": bool(source_ready),
        "integration": "ragflow",
        "product_name": "RAGFlow",
        "remote": REMOTE,
        "source_dir": str(SOURCE_DIR),
        "source_exists": SOURCE_DIR.exists(),
        "source_commit": commit,
        "source_branch": branch,
        "pinned_commit": PINNED_COMMIT,
        "source_file_count": sum(1 for p in SOURCE_DIR.rglob("*") if p.is_file() and ".git" not in p.parts) if SOURCE_DIR.exists() else 0,
        "version": _extract_pyproject_version(),
        "required_files_missing": missing_files,
        "home": str(HOME),
        "runtime_docker_dir": str(RUNTIME_DOCKER_DIR),
        "compose_file": str(COMPOSE_FILE),
        "compose_exists": COMPOSE_FILE.exists(),
        "env_file_exists": ENV_FILE.exists(),
        "env_summary": _env_key_summary(ENV_FILE) if ENV_FILE.exists() else None,
        "web_url": WEB_URL,
        "api_url": API_URL,
        "admin_url": ADMIN_URL,
        "mcp_url": MCP_URL,
        "web_health": web_health,
        "web_healthy": web_health.get("ok", False),
        "api_health": api_health,
        "api_healthy": api_health.get("ok", False),
        "machine": platform.machine(),
        "system": platform.system(),
        "docker": shutil.which("docker"),
        "docker_version": _tool_version(["docker", "--version"]),
        "docker_compose_version": _tool_version(["docker", "compose", "version"]),
        "uv": shutil.which("uv"),
        "uv_version": _tool_version(["uv", "--version"]),
        "go": shutil.which("go"),
        "go_version": _tool_version(["go", "version"]),
        "node": shutil.which("node"),
        "node_version": _tool_version(["node", "--version"]),
        "npm": shutil.which("npm"),
        "npm_version": _tool_version(["npm", "--version"]),
    }


def _extract_pyproject_version() -> str | None:
    path = SOURCE_DIR / "pyproject.toml"
    if not path.exists():
        return None
    for line in path.read_text(errors="replace").splitlines():
        if line.strip().startswith("version") and "=" in line:
            return line.split("=", 1)[1].strip().strip('"\'')
    return None


def doctor() -> dict[str, Any]:
    info = status()
    issues: list[str] = []
    warnings: list[str] = []
    if not info["source_exists"]:
        issues.append("RAGFlow source submodule is missing; run `git submodule update --init --recursive integrations/ragflow`.")
    elif info["source_commit"] != PINNED_COMMIT:
        issues.append(f"RAGFlow source is at {info['source_commit']}, expected {PINNED_COMMIT}.")
    if info["required_files_missing"]:
        issues.append(f"Required upstream files missing: {', '.join(info['required_files_missing'])}")
    if not info["docker"]:
        issues.append("Docker CLI is not on PATH; RAGFlow self-hosting requires Docker >= 24 and Docker Compose >= 2.26.1.")
    elif not info["docker_compose_version"]:
        issues.append("Docker Compose plugin is unavailable; `docker compose` commands will fail.")
    if not info["uv"]:
        warnings.append("uv is not on PATH; source-development setup requires uv and Python 3.13.")
    if not info["compose_exists"] or not info["env_file_exists"]:
        warnings.append("Hermes-local RAGFlow runtime files are not rendered yet; run `python scripts/ragflow_manage.py render-config`.")
    if info["machine"] in {"arm64", "aarch64"}:
        warnings.append("RAGFlow README cautions official Docker images are x86/amd64; on Apple Silicon you may need to build compatible images locally before `up`.")
    if not info["web_healthy"]:
        warnings.append(f"RAGFlow web UI is not responding at {info['web_url']}; start explicitly with `python scripts/ragflow_manage.py up` after reviewing resource needs.")
    if not info["api_healthy"]:
        warnings.append(f"RAGFlow API is not responding at {info['api_url']}; this is expected until the stack is started and initialized.")
    warnings.append("RAGFlow can pull/run multiple containers and needs >=16GB RAM and >=50GB disk; Hermes does not auto-start it.")
    warnings.append("Do not commit RAGFlow .env files, service_conf overrides with API keys, logs, Docker volumes, parsed documents, model caches, or database state.")
    return {"ok": not issues, "status": info, "issues": issues, "warnings": warnings}


def render_config() -> dict[str, Any]:
    source_docker = SOURCE_DIR / "docker"
    if not source_docker.exists():
        return {"ok": False, "error": f"missing source docker directory: {source_docker}"}
    HOME.mkdir(parents=True, exist_ok=True)
    RUNTIME_DOCKER_DIR.mkdir(parents=True, exist_ok=True)
    for name in [
        "docker-compose.yml",
        "docker-compose-base.yml",
        "service_conf.yaml.template",
        "entrypoint.sh",
        "init.sql",
        "infinity_conf.toml",
        "oceanbase-entrypoint.sh",
    ]:
        src = source_docker / name
        if src.exists():
            shutil.copy2(src, RUNTIME_DOCKER_DIR / name)
    _write_env_from_template(source_docker / ".env", ENV_FILE)
    (RUNTIME_DOCKER_DIR / "ragflow-logs").mkdir(exist_ok=True)
    return {
        "ok": True,
        "runtime_docker_dir": str(RUNTIME_DOCKER_DIR),
        "compose_file": str(COMPOSE_FILE),
        "env_file": str(ENV_FILE),
        "env_summary": _env_key_summary(ENV_FILE),
    }


def compose_config(timeout: int = 120) -> dict[str, Any]:
    if not COMPOSE_FILE.exists() or not ENV_FILE.exists():
        rendered = render_config()
        if not rendered.get("ok"):
            return rendered
    return _run_capture(["docker", "compose", "-f", str(COMPOSE_FILE), "config", "--quiet"], cwd=RUNTIME_DOCKER_DIR, timeout=timeout)


def up(timeout: int = 1200) -> dict[str, Any]:
    if not COMPOSE_FILE.exists() or not ENV_FILE.exists():
        rendered = render_config()
        if not rendered.get("ok"):
            return rendered
    return _run_capture(["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"], cwd=RUNTIME_DOCKER_DIR, timeout=timeout)


def down(timeout: int = 180) -> dict[str, Any]:
    if not COMPOSE_FILE.exists():
        return {"ok": False, "error": f"compose file does not exist: {COMPOSE_FILE}"}
    return _run_capture(["docker", "compose", "-f", str(COMPOSE_FILE), "down"], cwd=RUNTIME_DOCKER_DIR, timeout=timeout)


def wait_ready(timeout: int = 300) -> dict[str, Any]:
    deadline = time.time() + timeout
    last_web = None
    last_api = None
    while time.time() < deadline:
        last_web = _http_probe(WEB_URL, timeout=5)
        last_api = _http_probe(f"{API_URL}/v1/system/version", timeout=5)
        if last_web.get("ok") or last_api.get("ok"):
            return {"ok": True, "web_health": last_web, "api_health": last_api}
        time.sleep(5)
    return {"ok": False, "web_health": last_web, "api_health": last_api, "timeout": timeout}


def web_setup(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "install"], cwd=SOURCE_DIR / "web", timeout=timeout)


def web_build(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "run", "build"], cwd=SOURCE_DIR / "web", timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage RAGFlow as a Hermes external runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["status", "doctor", "render-config"]:
        sub.add_parser(name)
    for name, default in [("compose-config", 120), ("up", 1200), ("down", 180), ("wait-ready", 300), ("web-setup", 900), ("web-build", 900)]:
        p = sub.add_parser(name)
        p.add_argument("--timeout", type=int, default=default)
    args = parser.parse_args()
    handlers = {
        "status": status,
        "doctor": doctor,
        "render-config": render_config,
        "compose-config": lambda: compose_config(timeout=args.timeout),
        "up": lambda: up(timeout=args.timeout),
        "down": lambda: down(timeout=args.timeout),
        "wait-ready": lambda: wait_ready(timeout=args.timeout),
        "web-setup": lambda: web_setup(timeout=args.timeout),
        "web-build": lambda: web_build(timeout=args.timeout),
    }
    result = handlers[args.command]()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
