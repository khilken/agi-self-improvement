#!/usr/bin/env python3
"""Hermes manager for Background Agents / Open-Inspect.

Open-Inspect is a TypeScript/Python monorepo for hosted background coding agents.
Hermes keeps it as a pinned external source tree and operates through Node/npm,
Python/uv, Terraform/Wrangler, and HTTP boundaries rather than importing the app
into the Hermes Python runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "https://github.com/ColeMurray/background-agents.git"
PINNED_COMMIT = "122264349e461ae8f9f60e8d2c5573f9715b8972"
SOURCE_DIR = Path(os.environ.get("BACKGROUND_AGENTS_SOURCE_DIR", ROOT / "integrations" / "background-agents")).resolve()
HOME = Path(os.environ.get("HERMES_BACKGROUND_AGENTS_HOME", Path.home() / ".hermes" / "background-agents")).resolve()
WEB_URL = os.environ.get("BACKGROUND_AGENTS_WEB_URL", "http://127.0.0.1:3000").rstrip("/")

REQUIRED_FILES = [
    "README.md",
    "docs/SETUP_GUIDE.md",
    "docs/GETTING_STARTED.md",
    "docs/SECRETS.md",
    "package.json",
    "package-lock.json",
    "packages/control-plane/package.json",
    "packages/web/package.json",
    "packages/sandbox-runtime/pyproject.toml",
    "packages/modal-infra/pyproject.toml",
]

WORKSPACE_PACKAGES = [
    "@open-inspect/control-plane",
    "@open-inspect/web",
    "@open-inspect/shared",
    "@open-inspect/github-bot",
    "@open-inspect/slack-bot",
    "@open-inspect/linear-bot",
    "@open-inspect/opencomputer-infra",
]


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


def _read_package_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _web_probe(timeout: int = 3) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(WEB_URL, timeout=timeout) as response:
            body = response.read(200).decode("utf-8", errors="replace")
            return {"ok": 200 <= response.status < 400, "status": response.status, "url": WEB_URL, "body_preview": body}
    except Exception as exc:
        return {"ok": False, "status": None, "url": WEB_URL, "error": str(exc)}


def status() -> dict[str, Any]:
    commit = _git(["rev-parse", "HEAD"]).get("stdout", "") if SOURCE_DIR.exists() else ""
    branch = _git(["branch", "--show-current"]).get("stdout", "") if SOURCE_DIR.exists() else ""
    package = _read_package_json(SOURCE_DIR / "package.json") if SOURCE_DIR.exists() else {}
    missing_files = [rel for rel in REQUIRED_FILES if not (SOURCE_DIR / rel).exists()]
    health = _web_probe(timeout=2)
    source_ready = SOURCE_DIR.exists() and commit == PINNED_COMMIT and not missing_files
    return {
        "ok": bool(source_ready),
        "integration": "background-agents",
        "product_name": "Open-Inspect",
        "remote": REMOTE,
        "source_dir": str(SOURCE_DIR),
        "source_exists": SOURCE_DIR.exists(),
        "source_commit": commit,
        "source_branch": branch,
        "pinned_commit": PINNED_COMMIT,
        "source_file_count": sum(1 for p in SOURCE_DIR.rglob("*") if p.is_file() and ".git" not in p.parts) if SOURCE_DIR.exists() else 0,
        "package_name": package.get("name"),
        "version": package.get("version"),
        "workspaces": package.get("workspaces", []),
        "workspace_packages": WORKSPACE_PACKAGES,
        "required_files_missing": missing_files,
        "home": str(HOME),
        "web_url": WEB_URL,
        "web_health": health,
        "web_healthy": health.get("ok", False),
        "node": shutil.which("node"),
        "node_version": _tool_version(["node", "--version"]),
        "npm": shutil.which("npm"),
        "npm_version": _tool_version(["npm", "--version"]),
        "uv": shutil.which("uv"),
        "uv_version": _tool_version(["uv", "--version"]),
        "terraform": shutil.which("terraform"),
        "terraform_version": _tool_version(["terraform", "version", "-json"]),
        "wrangler": shutil.which("wrangler"),
        "wrangler_version": _tool_version(["wrangler", "--version"]),
        "node_modules_exists": (SOURCE_DIR / "node_modules").exists(),
        "modal_venv_exists": (SOURCE_DIR / "packages" / "modal-infra" / ".venv").exists(),
    }


def doctor() -> dict[str, Any]:
    info = status()
    issues: list[str] = []
    warnings: list[str] = []
    if not info["source_exists"]:
        issues.append("Background Agents source submodule is missing; run `git submodule update --init --recursive integrations/background-agents`.")
    elif info["source_commit"] != PINNED_COMMIT:
        issues.append(f"Background Agents source is at {info['source_commit']}, expected {PINNED_COMMIT}.")
    if info["required_files_missing"]:
        issues.append(f"Required upstream files missing: {', '.join(info['required_files_missing'])}")
    if not info["node"]:
        issues.append("Node.js is not on PATH; Open-Inspect requires Node.js 22+ for local development.")
    if not info["npm"]:
        issues.append("npm is not on PATH; Open-Inspect dependency setup/build commands require npm.")
    if not info["uv"]:
        warnings.append("uv is not on PATH; Python sandbox/modal-infra setup is optional but recommended.")
    if not info["terraform"]:
        warnings.append("Terraform is not on PATH; full self-hosted infrastructure deployment requires Terraform 1.9+.")
    if not info["wrangler"]:
        warnings.append("Wrangler is not on PATH; Cloudflare worker/R2/D1 deployment commands require wrangler.")
    if not info["node_modules_exists"]:
        warnings.append("Node dependencies are not installed; run `python scripts/background_agents_manage.py setup` before build/typecheck/test.")
    if not info["web_healthy"]:
        warnings.append(f"Open-Inspect web UI is not responding at {info['web_url']}; start it explicitly with `python scripts/background_agents_manage.py web-dev` after configuring env files.")
    warnings.append("Open-Inspect is single-tenant by design; deploy only behind trusted SSO/VPN and scoped GitHub App installations.")
    warnings.append("Do not commit Open-Inspect env files, Terraform tfvars/state, Cloudflare credentials, GitHub App secrets, OAuth tokens, or sandbox secrets.")
    return {"ok": not issues, "status": info, "issues": issues, "warnings": warnings}


def setup(timeout: int = 900) -> dict[str, Any]:
    HOME.mkdir(parents=True, exist_ok=True)
    return _run_capture(["npm", "ci"], cwd=SOURCE_DIR, timeout=timeout)


def build(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "run", "build"], cwd=SOURCE_DIR, timeout=timeout)


def typecheck(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "run", "typecheck"], cwd=SOURCE_DIR, timeout=timeout)


def test(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "test"], cwd=SOURCE_DIR, timeout=timeout)


def web_dev(timeout: int = 3600) -> dict[str, Any]:
    return _run_capture(["npm", "run", "dev", "-w", "@open-inspect/web"], cwd=SOURCE_DIR, timeout=timeout)


def web_build(timeout: int = 900) -> dict[str, Any]:
    return _run_capture(["npm", "run", "build", "-w", "@open-inspect/web"], cwd=SOURCE_DIR, timeout=timeout)


def shared_build(timeout: int = 300) -> dict[str, Any]:
    return _run_capture(["npm", "run", "build", "-w", "@open-inspect/shared"], cwd=SOURCE_DIR, timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Background Agents / Open-Inspect as a Hermes external runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["status", "doctor"]:
        sub.add_parser(name)
    for name, default in [("setup", 900), ("build", 900), ("typecheck", 900), ("test", 900), ("web-dev", 3600), ("web-build", 900), ("shared-build", 300)]:
        p = sub.add_parser(name)
        p.add_argument("--timeout", type=int, default=default)
    args = parser.parse_args()
    handlers = {
        "status": status,
        "doctor": doctor,
        "setup": lambda: setup(timeout=args.timeout),
        "build": lambda: build(timeout=args.timeout),
        "typecheck": lambda: typecheck(timeout=args.timeout),
        "test": lambda: test(timeout=args.timeout),
        "web-dev": lambda: web_dev(timeout=args.timeout),
        "web-build": lambda: web_build(timeout=args.timeout),
        "shared-build": lambda: shared_build(timeout=args.timeout),
    }
    result = handlers[args.command]()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
