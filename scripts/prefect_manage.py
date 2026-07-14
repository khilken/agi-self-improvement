#!/usr/bin/env python3
"""Hermes integration manager for Prefect.

Prefect is a full workflow orchestration runtime. Hermes tracks the upstream
source as a pinned submodule and manages Prefect through an isolated virtualenv
and process boundary instead of importing Prefect into the Hermes runtime.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "integrations" / "prefect"
DEFAULT_HOME = Path.home() / ".hermes" / "prefect"
PREFECT_REMOTE = "https://github.com/PrefectHQ/prefect.git"
PINNED_COMMIT = "0e7435055e18952aa8604dab78507b087a18defb"
DEFAULT_HOST = os.getenv("PREFECT_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("PREFECT_PORT", "4200"))
DEFAULT_TIMEOUT = 180


def source_dir() -> Path:
    return Path(os.getenv("PREFECT_SOURCE_DIR", str(DEFAULT_SOURCE_DIR))).expanduser().resolve()


def prefect_home() -> Path:
    return Path(os.getenv("HERMES_PREFECT_HOME", str(DEFAULT_HOME))).expanduser().resolve()


def venv_dir() -> Path:
    return Path(os.getenv("HERMES_PREFECT_VENV", str(prefect_home() / "venv"))).expanduser().resolve()


def prefect_api_url() -> str:
    return os.getenv("PREFECT_API_URL", f"http://{DEFAULT_HOST}:{DEFAULT_PORT}/api")


def ui_url() -> str:
    return os.getenv("HERMES_PREFECT_UI_URL", f"http://{DEFAULT_HOST}:{DEFAULT_PORT}")


def _run_capture(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int | None = DEFAULT_TIMEOUT,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
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
            "cmd": cmd,
        }
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": 127, "stdout": "", "stderr": str(exc), "cmd": cmd}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "ok": False,
            "returncode": -1,
            "stdout": stdout.strip(),
            "stderr": (stderr.strip() or f"Timed out after {timeout}s"),
            "cmd": cmd,
        }


def _git_value(args: list[str], cwd: Path) -> str | None:
    if not ((cwd / ".git").exists() or (cwd / ".git").is_file()):
        return None
    result = _run_capture(["git", *args], cwd=cwd, timeout=20)
    return result["stdout"] if result["ok"] else None


def python_bin() -> Path:
    return venv_dir() / "bin" / "python"


def prefect_bin() -> Path:
    return venv_dir() / "bin" / "prefect"


def _prefect_env(server: bool = False) -> dict[str, str]:
    home = prefect_home()
    home.mkdir(parents=True, exist_ok=True)
    runtime_home = home / "runtime"
    runtime_home.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    # Force state isolation. Inheriting a user/global Prefect profile can leak
    # runtime files into ~/.prefect or point Hermes smoke tests at a cloud/server
    # profile unexpectedly.
    env["PREFECT_HOME"] = str(runtime_home)
    env["PREFECT_PROFILES_PATH"] = str(runtime_home / "profiles.toml")
    env["PREFECT_MEMO_STORE_PATH"] = str(runtime_home / "memo_store.toml")
    env["PREFECT_LOCAL_STORAGE_PATH"] = str(runtime_home / "storage")
    env["PREFECT_LOGGING_SETTINGS_PATH"] = str(runtime_home / "logging.yml")
    env["PREFECT_SERVER_DATABASE_CONNECTION_URL"] = f"sqlite+aiosqlite:///{home / 'prefect.db'}"
    env.setdefault("PREFECT_LOGGING_LEVEL", "INFO")
    env["PREFECT_UI_URL"] = ui_url()
    if server:
        env.setdefault("PREFECT_SERVER_API_HOST", DEFAULT_HOST)
        env.setdefault("PREFECT_SERVER_API_PORT", str(DEFAULT_PORT))
    else:
        # Local flow smoke tests should not require a server unless the caller set one.
        env.pop("PREFECT_API_URL", None)
    env["PATH"] = f"{venv_dir() / 'bin'}:{env.get('PATH', '')}"
    return env


def _http_json(url: str, timeout: int = 5) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = raw[:1000]
            return {"ok": 200 <= response.status < 300, "status": response.status, "body": parsed}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def installed_version(timeout: int = 60) -> dict[str, Any]:
    py = python_bin()
    if not py.exists():
        return {"ok": False, "error": "Prefect venv is not initialized", "version": None}
    code = "import prefect, json; print(json.dumps({'version': prefect.__version__}))"
    result = _run_capture([str(py), "-c", code], timeout=timeout, env=_prefect_env())
    if result["ok"]:
        try:
            result["version"] = json.loads(result["stdout"])["version"]
        except Exception:
            result["version"] = result["stdout"]
    else:
        result["version"] = None
    return result


def status() -> dict[str, Any]:
    src = source_dir()
    home = prefect_home()
    py = python_bin()
    cli = prefect_bin()
    version = installed_version(timeout=30) if py.exists() else {"ok": False, "version": None}
    server_health = _http_json(f"{prefect_api_url().rstrip('/')}/health", timeout=3)
    return {
        "integration": "prefect",
        "remote": PREFECT_REMOTE,
        "pinned_commit": PINNED_COMMIT,
        "source_dir": str(src),
        "source_exists": src.exists(),
        "source_commit": _git_value(["rev-parse", "HEAD"], src) if src.exists() else None,
        "source_branch": _git_value(["branch", "--show-current"], src) if src.exists() else None,
        "home": str(home),
        "venv": str(venv_dir()),
        "venv_exists": py.exists(),
        "python": str(py) if py.exists() else None,
        "prefect_cli": str(cli) if cli.exists() else None,
        "prefect_installed": bool(version.get("ok")),
        "prefect_version": version.get("version"),
        "uv": shutil.which("uv"),
        "system_python": sys.executable,
        "api_url": prefect_api_url(),
        "ui_url": ui_url(),
        "server_healthy": bool(server_health.get("ok")),
        "server_health": server_health,
    }


def doctor() -> dict[str, Any]:
    info = status()
    issues: list[str] = []
    warnings: list[str] = []
    if not info["source_exists"]:
        issues.append("Prefect source submodule is missing; run `git submodule update --init --recursive integrations/prefect`.")
    elif info["source_commit"] != PINNED_COMMIT:
        warnings.append(f"Prefect source is at {info['source_commit']}, expected pinned commit {PINNED_COMMIT}.")
    if not info["venv_exists"]:
        warnings.append("Prefect isolated virtualenv is not initialized; run `python scripts/prefect_manage.py setup`.")
    elif not info["prefect_installed"]:
        warnings.append("Prefect virtualenv exists but `import prefect` failed; rerun setup.")
    if not info["server_healthy"]:
        warnings.append(f"Prefect server is not responding at {info['api_url']}; start with `python scripts/prefect_manage.py server` if UI/API orchestration is needed.")
    return {"ok": not issues, "status": info, "issues": issues, "warnings": warnings}


def setup(timeout: int = 1200, editable: bool = True) -> dict[str, Any]:
    src = source_dir()
    if not src.exists():
        return {"ok": False, "error": f"Source directory not found: {src}"}
    home = prefect_home()
    home.mkdir(parents=True, exist_ok=True)
    venv = venv_dir()
    steps: list[dict[str, Any]] = []

    if not python_bin().exists():
        uv = shutil.which("uv")
        if uv:
            steps.append(_run_capture([uv, "venv", str(venv), "--python", sys.executable], timeout=180))
        else:
            steps.append(_run_capture([sys.executable, "-m", "venv", str(venv)], timeout=180))
        if not steps[-1].get("ok"):
            return {"ok": False, "home": str(home), "venv": str(venv), "steps": steps}

    uv = shutil.which("uv")
    if uv:
        install_target = f"-e{src}" if editable else str(src)
        steps.append(_run_capture([uv, "pip", "install", "--python", str(python_bin()), install_target], cwd=src, timeout=timeout, env=_prefect_env()))
    else:
        install_target = f"-e{src}" if editable else str(src)
        steps.append(_run_capture([str(python_bin()), "-m", "pip", "install", "--upgrade", "pip"], timeout=300, env=_prefect_env()))
        steps.append(_run_capture([str(python_bin()), "-m", "pip", "install", install_target], cwd=src, timeout=timeout, env=_prefect_env()))

    version = installed_version(timeout=120)
    ok = all(step.get("ok", False) for step in steps) and bool(version.get("ok"))
    return {"ok": ok, "home": str(home), "venv": str(venv), "steps": steps, "version": version}


def cli(args: Iterable[str], timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    binary = prefect_bin()
    if not binary.exists():
        return {"ok": False, "returncode": 127, "stdout": "", "stderr": "Prefect CLI not found. Run setup first.", "cmd": [str(binary), *list(args)]}
    return _run_capture([str(binary), *list(args)], timeout=timeout, env=_prefect_env())


def smoke(timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    py = python_bin()
    if not py.exists():
        return {"ok": False, "error": "Prefect venv is not initialized; run setup first."}
    script = textwrap.dedent(
        """
        from prefect import flow, task

        @task(retries=1, log_prints=True)
        def add_one(x: int) -> int:
            print(f"task input={x}")
            return x + 1

        @flow(name="hermes-prefect-smoke", log_prints=True)
        def hermes_prefect_smoke() -> int:
            value = add_one(41)
            print(f"flow result={value}")
            return value

        result = hermes_prefect_smoke()
        print(f"HERMES_PREFECT_SMOKE_RESULT={result}")
        assert result == 42
        """
    ).strip()
    result = _run_capture([str(py), "-c", script], timeout=timeout, env=_prefect_env())
    result["smoke_passed"] = result.get("ok") and "HERMES_PREFECT_SMOKE_RESULT=42" in result.get("stdout", "")
    result["ok"] = bool(result["smoke_passed"])
    return result


def server(timeout: int | None = None) -> dict[str, Any]:
    binary = prefect_bin()
    if not binary.exists():
        return {"ok": False, "error": "Prefect CLI not found. Run setup first."}
    # This is intended for Hermes background terminal management. The process is
    # long-lived, so the default must not include an internal kill-switch timeout.
    return _run_capture(
        [str(binary), "server", "start", "--host", DEFAULT_HOST, "--port", str(DEFAULT_PORT)],
        timeout=timeout,
        env=_prefect_env(server=True),
    )


def wait_ready(timeout: int = 60) -> dict[str, Any]:
    deadline = time.time() + timeout
    health_url = f"{prefect_api_url().rstrip('/')}/health"
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = _http_json(health_url, timeout=5)
        if last.get("ok"):
            return {"ok": True, "health_url": health_url, "health": last}
        time.sleep(1)
    return {"ok": False, "health_url": health_url, "last": last}


def emit(data: dict[str, Any]) -> int:
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0 if data.get("ok", True) else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the Prefect external workflow orchestration integration.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("doctor")

    setup_p = sub.add_parser("setup")
    setup_p.add_argument("--timeout", type=int, default=1200)
    setup_p.add_argument("--no-editable", action="store_true")

    cli_p = sub.add_parser("cli")
    cli_p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    cli_p.add_argument("args", nargs=argparse.REMAINDER)

    smoke_p = sub.add_parser("smoke")
    smoke_p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)

    server_p = sub.add_parser("server")
    server_p.add_argument("--timeout", type=int, default=0, help="Internal timeout in seconds; 0 disables timeout for daemon use")

    wait_p = sub.add_parser("wait-ready")
    wait_p.add_argument("--timeout", type=int, default=60)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "status":
        return emit(status())
    if args.command == "doctor":
        return emit(doctor())
    if args.command == "setup":
        return emit(setup(timeout=args.timeout, editable=not args.no_editable))
    if args.command == "cli":
        cli_args = args.args[1:] if args.args[:1] == ["--"] else args.args
        return emit(cli(cli_args, timeout=args.timeout))
    if args.command == "smoke":
        return emit(smoke(timeout=args.timeout))
    if args.command == "server":
        return emit(server(timeout=args.timeout or None))
    if args.command == "wait-ready":
        return emit(wait_ready(timeout=args.timeout))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
