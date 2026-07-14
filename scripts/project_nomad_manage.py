#!/usr/bin/env python3
"""Hermes manager for Project N.O.M.A.D.

Project N.O.M.A.D. is a Docker/Node offline-first knowledge server. Hermes keeps
it as a pinned external source tree and manages it through Docker/Node/HTTP
boundaries instead of importing its application code into Hermes.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NOMAD_REMOTE = "https://github.com/Crosstalk-Solutions/project-nomad.git"
PINNED_COMMIT = "6a4f02dd4626c64f38ac07e4740bc250ba13fea1"
SOURCE_DIR = Path(os.environ.get("PROJECT_NOMAD_SOURCE_DIR", ROOT / "integrations" / "project-nomad")).resolve()
HOME = Path(os.environ.get("HERMES_PROJECT_NOMAD_HOME", Path.home() / ".hermes" / "project-nomad")).resolve()
COMPOSE_PATH = Path(os.environ.get("PROJECT_NOMAD_COMPOSE", HOME / "docker-compose.yml")).resolve()
STORAGE_DIR = Path(os.environ.get("PROJECT_NOMAD_STORAGE", HOME / "storage")).resolve()
BASE_URL = os.environ.get("PROJECT_NOMAD_URL", "http://127.0.0.1:8080").rstrip("/")


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


def _health(timeout: int = 5) -> dict[str, Any]:
    url = f"{BASE_URL}/api/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")[:500]
            return {"ok": 200 <= response.status < 300, "status": response.status, "body": body, "url": url}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc), "url": url}


def _node_version() -> str | None:
    result = _run_capture(["node", "--version"], timeout=10)
    return result["stdout"] if result.get("ok") else None


def _npm_version() -> str | None:
    result = _run_capture(["npm", "--version"], timeout=10)
    return result["stdout"] if result.get("ok") else None


def _docker_version() -> str | None:
    result = _run_capture(["docker", "--version"], timeout=10)
    return result["stdout"] if result.get("ok") else None


def _docker_compose_version() -> str | None:
    result = _run_capture(["docker", "compose", "version"], timeout=10)
    return result["stdout"] if result.get("ok") else None


def status() -> dict[str, Any]:
    commit = _git(["rev-parse", "HEAD"]).get("stdout", "") if SOURCE_DIR.exists() else ""
    branch = _git(["branch", "--show-current"]).get("stdout", "") if SOURCE_DIR.exists() else ""
    package_json = SOURCE_DIR / "package.json"
    admin_package_json = SOURCE_DIR / "admin" / "package.json"
    compose_template = SOURCE_DIR / "install" / "management_compose.yaml"
    version = None
    if package_json.exists():
        try:
            version = json.loads(package_json.read_text())["version"]
        except Exception:
            version = None
    health = _health(timeout=2)
    source_ready = SOURCE_DIR.exists() and commit == PINNED_COMMIT
    return {
        "ok": bool(source_ready),
        "integration": "project-nomad",
        "remote": NOMAD_REMOTE,
        "source_dir": str(SOURCE_DIR),
        "source_exists": SOURCE_DIR.exists(),
        "source_commit": commit,
        "source_branch": branch,
        "pinned_commit": PINNED_COMMIT,
        "source_file_count": sum(1 for p in SOURCE_DIR.rglob("*") if p.is_file() and ".git" not in p.parts) if SOURCE_DIR.exists() else 0,
        "version": version,
        "home": str(HOME),
        "storage_dir": str(STORAGE_DIR),
        "compose_path": str(COMPOSE_PATH),
        "compose_exists": COMPOSE_PATH.exists(),
        "base_url": BASE_URL,
        "server_health": health,
        "server_healthy": health.get("ok", False),
        "package_json_exists": package_json.exists(),
        "admin_package_json_exists": admin_package_json.exists(),
        "compose_template_exists": compose_template.exists(),
        "node": shutil.which("node"),
        "node_version": _node_version(),
        "npm": shutil.which("npm"),
        "npm_version": _npm_version(),
        "docker": shutil.which("docker"),
        "docker_version": _docker_version(),
        "docker_compose_version": _docker_compose_version(),
    }


def doctor() -> dict[str, Any]:
    info = status()
    issues: list[str] = []
    warnings: list[str] = []
    if not info["source_exists"]:
        issues.append("Project Nomad source submodule is missing; run `git submodule update --init --recursive integrations/project-nomad`.")
    elif info["source_commit"] != PINNED_COMMIT:
        issues.append(f"Project Nomad source is at {info['source_commit']}, expected {PINNED_COMMIT}.")
    if not info["package_json_exists"] or not info["admin_package_json_exists"]:
        issues.append("Project Nomad package manifests are missing from the source tree.")
    if not info["compose_template_exists"]:
        issues.append("Project Nomad Docker Compose template is missing from install/management_compose.yaml.")
    if not info["node"]:
        warnings.append("Node.js is not on PATH; admin source setup/build commands need Node 22+.")
    if not info["npm"]:
        warnings.append("npm is not on PATH; admin dependency setup needs npm.")
    if not info["docker"]:
        warnings.append("Docker CLI is not on PATH; containerized Nomad startup requires Docker.")
    elif not info["docker_compose_version"]:
        warnings.append("Docker Compose plugin is unavailable; `docker compose` commands will fail.")
    if not info["compose_exists"]:
        warnings.append("Local Hermes Project Nomad compose file has not been rendered yet; run `python scripts/project_nomad_manage.py render-compose`.")
    if not info["server_healthy"]:
        warnings.append(f"Project Nomad is not responding at {info['base_url']}; start it explicitly with `python scripts/project_nomad_manage.py up` after rendering compose.")
    return {"ok": not issues, "status": info, "issues": issues, "warnings": warnings}


def render_compose() -> dict[str, Any]:
    template = SOURCE_DIR / "install" / "management_compose.yaml"
    if not template.exists():
        return {"ok": False, "error": f"missing compose template: {template}"}
    HOME.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    mysql_dir = HOME / "mysql"
    redis_dir = HOME / "redis"
    mysql_dir.mkdir(parents=True, exist_ok=True)
    redis_dir.mkdir(parents=True, exist_ok=True)
    text = template.read_text()
    app_key = os.environ.get("PROJECT_NOMAD_APP_KEY", "hermes-project-nomad-local-dev-key")
    db_password = os.environ.get("PROJECT_NOMAD_DB_PASSWORD", "hermes-project-nomad-db-password")
    root_password = os.environ.get("PROJECT_NOMAD_MYSQL_ROOT_PASSWORD", "hermes-project-nomad-root-password")
    replacements = {
        "/opt/project-nomad/storage": str(STORAGE_DIR),
        "/opt/project-nomad/mysql": str(mysql_dir),
        "/opt/project-nomad/redis": str(redis_dir),
        "/opt/project-nomad": str(HOME),
        "APP_KEY=replaceme": f"APP_KEY={app_key}",
        "URL=replaceme": f"URL={BASE_URL}",
        "DB_PASSWORD=replaceme": f"DB_PASSWORD={db_password}",
        "MYSQL_ROOT_PASSWORD=replaceme": f"MYSQL_ROOT_PASSWORD={root_password}",
        "MYSQL_PASSWORD=replaceme": f"MYSQL_PASSWORD={db_password}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    COMPOSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPOSE_PATH.write_text(text)
    return {"ok": True, "compose_path": str(COMPOSE_PATH), "home": str(HOME), "storage_dir": str(STORAGE_DIR)}


def compose_config(timeout: int = 60) -> dict[str, Any]:
    if not COMPOSE_PATH.exists():
        rendered = render_compose()
        if not rendered.get("ok"):
            return rendered
    return _run_capture(["docker", "compose", "-f", str(COMPOSE_PATH), "config", "--quiet"], timeout=timeout)


def up(timeout: int = 600) -> dict[str, Any]:
    if not COMPOSE_PATH.exists():
        rendered = render_compose()
        if not rendered.get("ok"):
            return rendered
    return _run_capture(["docker", "compose", "-f", str(COMPOSE_PATH), "up", "-d"], timeout=timeout)


def down(timeout: int = 120) -> dict[str, Any]:
    if not COMPOSE_PATH.exists():
        return {"ok": False, "error": f"compose file does not exist: {COMPOSE_PATH}"}
    return _run_capture(["docker", "compose", "-f", str(COMPOSE_PATH), "down"], timeout=timeout)


def wait_ready(timeout: int = 120) -> dict[str, Any]:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = _health(timeout=5)
        if last.get("ok"):
            return {"ok": True, "health": last, "health_url": last["url"]}
        time.sleep(2)
    return {"ok": False, "health": last, "health_url": f"{BASE_URL}/api/health", "timeout": timeout}


def npm_setup(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "ci"], cwd=SOURCE_DIR / "admin", timeout=timeout)


def npm_build(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "run", "build"], cwd=SOURCE_DIR / "admin", timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Project N.O.M.A.D. as a Hermes external runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("doctor")
    sub.add_parser("render-compose")
    cfg = sub.add_parser("compose-config")
    cfg.add_argument("--timeout", type=int, default=60)
    setup_p = sub.add_parser("setup")
    setup_p.add_argument("--timeout", type=int, default=900)
    build_p = sub.add_parser("build")
    build_p.add_argument("--timeout", type=int, default=900)
    up_p = sub.add_parser("up")
    up_p.add_argument("--timeout", type=int, default=600)
    down_p = sub.add_parser("down")
    down_p.add_argument("--timeout", type=int, default=120)
    wait_p = sub.add_parser("wait-ready")
    wait_p.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    handlers = {
        "status": status,
        "doctor": doctor,
        "render-compose": render_compose,
        "compose-config": lambda: compose_config(timeout=args.timeout),
        "setup": lambda: npm_setup(timeout=args.timeout),
        "build": lambda: npm_build(timeout=args.timeout),
        "up": lambda: up(timeout=args.timeout),
        "down": lambda: down(timeout=args.timeout),
        "wait-ready": lambda: wait_ready(timeout=args.timeout),
    }
    result = handlers[args.command]()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
