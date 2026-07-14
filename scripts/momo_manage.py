#!/usr/bin/env python3
"""Hermes integration manager for the Momo AI memory system.

Momo is a standalone Rust service exposing REST and MCP endpoints. Hermes keeps
it behind a process/network boundary instead of importing Rust internals into the
Python runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "integrations" / "momo"
DEFAULT_TIMEOUT = 120
MOMO_REMOTE = "https://github.com/momomemory/momo.git"
PINNED_COMMIT = "3f32cd6069fe1491659e6fbd76af717a167b6741"
DEFAULT_HOME = Path.home() / ".momo"
DEFAULT_PORT = int(os.getenv("MOMO_PORT", "3333"))
DEFAULT_HOST = os.getenv("MOMO_HOST", "127.0.0.1")
DEFAULT_API_KEY = os.getenv("MOMO_API_KEY") or os.getenv("HERMES_MOMO_API_KEY") or "hermes-dev-key"


def source_dir() -> Path:
    return Path(os.getenv("MOMO_SOURCE_DIR", str(DEFAULT_SOURCE_DIR))).expanduser().resolve()


def momo_home() -> Path:
    return Path(os.getenv("MOMO_HOME", str(DEFAULT_HOME))).expanduser().resolve()


def base_url() -> str:
    return os.getenv("MOMO_BASE_URL", f"http://{DEFAULT_HOST}:{DEFAULT_PORT}").rstrip("/")


def _run_capture(cmd: list[str], cwd: Path | None = None, timeout: int | None = 15, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": f"Timed out after {timeout}s",
        }


def _version(binary: str) -> str | None:
    path = shutil.which(binary)
    if not path:
        return None
    result = _run_capture([binary, "--version"], timeout=10)
    return result["stdout"] or result["stderr"] or path


def _git_value(args: list[str], cwd: Path) -> str | None:
    if not (cwd / ".git").exists() and not (cwd / ".git").is_file():
        return None
    result = _run_capture(["git", *args], cwd=cwd, timeout=15)
    return result["stdout"] if result["ok"] else None


def find_momo_binary(src: Path | None = None) -> Path | None:
    """Find a usable Momo executable without installing anything."""
    env_bin = os.getenv("MOMO_BIN")
    if env_bin:
        p = Path(env_bin).expanduser().resolve()
        if p.exists() and os.access(p, os.X_OK):
            return p

    if src is None:
        src = source_dir()
    for candidate in [src / "target" / "release" / "momo", src / "target" / "debug" / "momo"]:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate

    path_bin = shutil.which("momo")
    return Path(path_bin).resolve() if path_bin else None


def _service_env() -> dict[str, str]:
    home = momo_home()
    home.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("MOMO_HOST", DEFAULT_HOST)
    env.setdefault("MOMO_PORT", str(DEFAULT_PORT))
    env.setdefault("MOMO_API_KEYS", DEFAULT_API_KEY)
    env.setdefault("DATABASE_URL", f"file:{home / 'momo.db'}")
    # Use local Ollama for optional LLM-backed inference if Momo needs it.
    env.setdefault("LLM_MODEL", "ollama/qwen2.5:14b")
    env.setdefault("LLM_BASE_URL", "http://192.168.1.111:11434/v1")
    return env


def _http_json(path: str, method: str = "GET", body: dict[str, Any] | None = None, timeout: int = 20, auth: bool = False) -> dict[str, Any]:
    url = f"{base_url()}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if auth:
        headers["Authorization"] = f"Bearer {DEFAULT_API_KEY}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            parsed = json.loads(raw) if raw else None
            return {"ok": 200 <= response.status < 300, "status_code": response.status, "url": url, "data": parsed}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw
        return {"ok": False, "status_code": exc.code, "url": url, "error": parsed}
    except Exception as exc:
        return {"ok": False, "status_code": None, "url": url, "error": f"{type(exc).__name__}: {exc}"}


def health(timeout: int = 10) -> dict[str, Any]:
    return _http_json("/api/v1/health", timeout=timeout)


def status() -> dict[str, Any]:
    src = source_dir()
    binary = find_momo_binary(src)
    cargo = shutil.which("cargo")
    rustc = shutil.which("rustc")
    commit = _git_value(["rev-parse", "HEAD"], src) if src.exists() else None
    branch = _git_value(["branch", "--show-current"], src) if src.exists() else None
    files = _git_value(["ls-files"], src) if src.exists() else None
    service_health = health(timeout=3)

    return {
        "integration": "momo",
        "remote": MOMO_REMOTE,
        "pinned_commit": PINNED_COMMIT,
        "source_dir": str(src),
        "source_exists": src.exists(),
        "source_commit": commit,
        "source_branch": branch or "detached" if commit else None,
        "source_file_count": len(files.splitlines()) if files else 0,
        "binary_path": str(binary) if binary else None,
        "binary_available": binary is not None,
        "cargo_path": cargo,
        "rustc_path": rustc,
        "cargo_version": _version("cargo"),
        "rustc_version": _version("rustc"),
        "can_build": bool(cargo and rustc and src.exists()),
        "home": str(momo_home()),
        "base_url": base_url(),
        "api_key_source": "MOMO_API_KEY/HERMES_MOMO_API_KEY" if (os.getenv("MOMO_API_KEY") or os.getenv("HERMES_MOMO_API_KEY")) else "default-dev-key",
        "service_healthy": bool(service_health.get("ok")),
        "service_health": service_health,
    }


def doctor() -> dict[str, Any]:
    info = status()
    issues: list[str] = []
    warnings: list[str] = []

    if not info["source_exists"]:
        issues.append("Momo source submodule is missing; run `git submodule update --init --recursive integrations/momo`.")
    elif info["source_commit"] != PINNED_COMMIT:
        warnings.append(f"Momo source is at {info['source_commit']}, expected pinned commit {PINNED_COMMIT}.")

    if not info["binary_available"]:
        warnings.append("No `momo` executable found. Build with `python scripts/momo_manage.py build` after installing Rust, or set MOMO_BIN.")

    if not info["cargo_path"] or not info["rustc_path"]:
        warnings.append("Rust toolchain is not installed or not on PATH; build actions are unavailable on this host.")

    if not info["service_healthy"]:
        warnings.append(f"Momo service is not responding at {info['base_url']}; start it with `python scripts/momo_manage.py serve`.")

    ok = bool(info["source_exists"] and (info["binary_available"] or info["can_build"]))
    return {"ok": ok, "status": info, "issues": issues, "warnings": warnings}


def build(release: bool = True, timeout: int = 900) -> dict[str, Any]:
    src = source_dir()
    if not src.exists():
        return {"ok": False, "error": f"Missing source directory: {src}"}
    if not shutil.which("cargo"):
        return {"ok": False, "error": "cargo is not installed or not on PATH"}
    cmd = ["cargo", "build"]
    if release:
        cmd.append("--release")
    result = _run_capture(cmd, cwd=src, timeout=timeout, env=_service_env())
    result["cmd"] = cmd
    result["cwd"] = str(src)
    result["binary_path"] = str(find_momo_binary(src)) if result["ok"] and find_momo_binary(src) else None
    return result


def run_momo(args: Iterable[str], timeout: int | None = DEFAULT_TIMEOUT) -> dict[str, Any]:
    binary = find_momo_binary()
    if not binary:
        return {
            "ok": False,
            "returncode": 127,
            "stdout": "",
            "stderr": "No momo executable found. Build from integrations/momo or set MOMO_BIN.",
        }
    cmd = [str(binary), *list(args)]
    result = _run_capture(cmd, cwd=momo_home(), timeout=timeout, env=_service_env())
    result["cmd"] = cmd
    return result


def serve(timeout: int | None = None, single_process: bool = True) -> dict[str, Any]:
    """Run the Momo HTTP service in the foreground until killed by caller.

    Use ``timeout=None`` for daemon operation. Hermes should supervise long-lived
    services with its background-process tracker rather than an internal
    subprocess timeout that eventually kills an otherwise healthy server.
    """
    args = ["--mode", "api"]
    if single_process:
        args.append("--single-process")
    return run_momo(args, timeout=timeout)


def wait_ready(timeout: int = 30) -> dict[str, Any]:
    deadline = time.time() + timeout
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = health(timeout=3)
        if last.get("ok"):
            return {"ok": True, "health": last}
        time.sleep(1)
    return {"ok": False, "health": last, "error": f"Momo did not become healthy within {timeout}s"}


def ingest_conversation(messages: list[dict[str, str]], container_tag: str = "hermes", timeout: int = 60) -> dict[str, Any]:
    payload = {"messages": messages, "containerTag": container_tag}
    return _http_json("/api/v1/conversations:ingest", method="POST", body=payload, timeout=timeout, auth=True)


def create_document(
    content: str,
    container_tag: str = "hermes",
    title: str | None = None,
    custom_id: str | None = None,
    content_type: str = "text/plain",
    extract_memories: bool = False,
    timeout: int = 60,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "content": content,
        "containerTag": container_tag,
        "contentType": content_type,
        "extractMemories": extract_memories,
        "metadata": {"source": "hermes"},
    }
    if title:
        payload["title"] = title
    if custom_id:
        payload["customId"] = custom_id
    return _http_json("/api/v1/documents", method="POST", body=payload, timeout=timeout, auth=True)


def list_documents(container_tags: list[str] | None = None, limit: int = 20, timeout: int = 30) -> dict[str, Any]:
    params = [f"limit={max(1, min(limit, 100))}"]
    for tag in container_tags or []:
        params.append(f"containerTags={urllib.parse.quote(tag)}")
    return _http_json(f"/api/v1/documents?{'&'.join(params)}", timeout=timeout, auth=True)


def search(query: str, container_tags: list[str] | None = None, scope: str = "hybrid", limit: int = 10, timeout: int = 60) -> dict[str, Any]:
    payload: dict[str, Any] = {"q": query, "scope": scope, "limit": limit}
    if container_tags:
        payload["containerTags"] = container_tags
    return _http_json("/api/v1/search", method="POST", body=payload, timeout=timeout, auth=True)


def emit(data: dict[str, Any], as_json: bool = True) -> int:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(data)
    return 0 if data.get("ok", True) else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the Momo memory subsystem integrated into Hermes.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show source/toolchain/binary/service status as JSON")
    sub.add_parser("doctor", help="Run non-mutating integration diagnostics")
    sub.add_parser("health", help="Check the Momo REST health endpoint")

    build_p = sub.add_parser("build", help="Build Momo from the pinned submodule source")
    build_p.add_argument("--debug", action="store_true", help="Build debug profile instead of release")
    build_p.add_argument("--timeout", type=int, default=900)

    serve_p = sub.add_parser("serve", help="Run the Momo HTTP service in the foreground")
    serve_p.add_argument("--timeout", type=int, default=0, help="Internal timeout in seconds; 0 disables timeout for daemon use")
    serve_p.add_argument("--supervisor", action="store_true", help="Use Momo supervisor mode instead of API-only single process")

    wait_p = sub.add_parser("wait-ready", help="Wait for the Momo HTTP service to become healthy")
    wait_p.add_argument("--timeout", type=int, default=30)

    ingest_p = sub.add_parser("ingest", help="Ingest a single user text as conversation memory")
    ingest_p.add_argument("text")
    ingest_p.add_argument("--container-tag", default="hermes")
    ingest_p.add_argument("--timeout", type=int, default=60)

    doc_p = sub.add_parser("document", help="Create a text document in Momo")
    doc_p.add_argument("content")
    doc_p.add_argument("--container-tag", default="hermes")
    doc_p.add_argument("--title")
    doc_p.add_argument("--custom-id")
    doc_p.add_argument("--content-type", default="text/plain")
    doc_p.add_argument("--extract-memories", action="store_true")
    doc_p.add_argument("--timeout", type=int, default=60)

    docs_p = sub.add_parser("documents", help="List Momo documents")
    docs_p.add_argument("--container-tag", action="append", dest="container_tags")
    docs_p.add_argument("--limit", type=int, default=20)
    docs_p.add_argument("--timeout", type=int, default=30)

    search_p = sub.add_parser("search", help="Search Momo memories/documents")
    search_p.add_argument("query")
    search_p.add_argument("--container-tag", action="append", dest="container_tags")
    search_p.add_argument("--scope", default="hybrid", choices=["hybrid", "documents", "memories"])
    search_p.add_argument("--limit", type=int, default=10)
    search_p.add_argument("--timeout", type=int, default=60)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "status":
        return emit(status())
    if args.command == "doctor":
        return emit(doctor())
    if args.command == "health":
        return emit(health())
    if args.command == "build":
        return emit(build(release=not args.debug, timeout=args.timeout))
    if args.command == "serve":
        return emit(serve(timeout=args.timeout or None, single_process=not args.supervisor))
    if args.command == "wait-ready":
        return emit(wait_ready(timeout=args.timeout))
    if args.command == "ingest":
        return emit(ingest_conversation([{"role": "user", "content": args.text}], container_tag=args.container_tag, timeout=args.timeout))
    if args.command == "document":
        return emit(create_document(
            args.content,
            container_tag=args.container_tag,
            title=args.title,
            custom_id=args.custom_id,
            content_type=args.content_type,
            extract_memories=args.extract_memories,
            timeout=args.timeout,
        ))
    if args.command == "documents":
        return emit(list_documents(container_tags=args.container_tags, limit=args.limit, timeout=args.timeout))
    if args.command == "search":
        return emit(search(args.query, container_tags=args.container_tags, scope=args.scope, limit=args.limit, timeout=args.timeout))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
