#!/usr/bin/env python3
"""Hermes integration manager for Shubhamsaboo/awesome-llm-apps.

The upstream repository is a large cookbook of independent Python, Node, RAG,
MCP, voice, and agent-skill templates. Hermes tracks it as an external source
collection and manages individual templates across process/environment
boundaries instead of importing all template code into the Hermes runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "integrations" / "awesome-llm-apps"
DEFAULT_HOME = Path.home() / ".hermes" / "awesome-llm-apps"
REMOTE = "https://github.com/Shubhamsaboo/awesome-llm-apps.git"
PINNED_COMMIT = "426cfa66b5fd832090038c36e50a6aa1dab3119c"

CATEGORY_LABELS = {
    "agent_skills": "Agent Skills",
    "starter_ai_agents": "Starter AI Agents",
    "advanced_ai_agents": "Advanced AI Agents",
    "always_on_agents": "Always-on Agents",
    "mcp_ai_agents": "MCP AI Agents",
    "voice_ai_agents": "Voice AI Agents",
    "generative_ui_agents": "Generative UI Agents",
    "rag_tutorials": "RAG Tutorials",
    "advanced_llm_apps": "Advanced LLM Apps",
    "ai_agent_framework_crash_course": "Agent Framework Crash Courses",
}

ENTRYPOINT_PREFERENCE = [
    "app.py",
    "main.py",
    "server.py",
    "streamlit_app.py",
    "agent.py",
    "agents.py",
]


def source_dir() -> Path:
    return Path(os.getenv("AWESOME_LLM_APPS_SOURCE_DIR", str(DEFAULT_SOURCE_DIR))).expanduser().resolve()


def integration_home() -> Path:
    return Path(os.getenv("AWESOME_LLM_APPS_HOME", str(DEFAULT_HOME))).expanduser().resolve()


def _run_capture(cmd: list[str], cwd: Path | None = None, timeout: int = 60, env: dict[str, str] | None = None) -> dict[str, Any]:
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


def _git_value(args: list[str], cwd: Path) -> str | None:
    if not ((cwd / ".git").exists() or (cwd / ".git").is_file()):
        return None
    result = _run_capture(["git", *args], cwd=cwd, timeout=15)
    return result["stdout"] if result["ok"] else None


def _read_title(directory: Path) -> str | None:
    for name in ("README.md", "readme.md"):
        readme = directory / name
        if not readme.exists():
            continue
        for line in readme.read_text(errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    return None


def _is_external_noise(path: Path) -> bool:
    return ".git" in path.parts or "node_modules" in path.parts or "__pycache__" in path.parts


def _slug(path: str) -> str:
    base = path.replace("/", "__").replace(".", "_").replace("-", "_")
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]
    return f"{base}__{digest}"


def _python_entrypoints(directory: Path) -> list[str]:
    py_files = sorted(p.name for p in directory.glob("*.py"))
    preferred = [name for name in ENTRYPOINT_PREFERENCE if name in py_files]
    agent_like = [name for name in py_files if "agent" in name.lower() and name not in preferred]
    app_like = [name for name in py_files if name not in preferred and name not in agent_like and not name.startswith("__")]
    return [*preferred, *agent_like, *app_like]


def _detect_launchers(directory: Path) -> dict[str, Any]:
    py_entries = _python_entrypoints(directory)
    launchers: dict[str, Any] = {}
    if py_entries:
        primary = py_entries[0]
        launchers["python"] = [sys.executable, primary]
        if primary in {"app.py", "streamlit_app.py"} or "streamlit" in primary.lower():
            launchers["streamlit"] = ["streamlit", "run", primary]
    if (directory / "package.json").exists():
        launchers["node"] = ["npm", "run", "dev"]
    if (directory / "README.md").exists() and "agent_skills" in directory.parts:
        launchers["skill"] = ["readme"]
    return launchers


def discover_catalog() -> list[dict[str, Any]]:
    root = source_dir()
    if not root.exists():
        return []

    markers = {
        "requirements.txt",
        "pyproject.toml",
        "package.json",
        "app.py",
        "main.py",
        "server.py",
        "streamlit_app.py",
    }
    items: list[dict[str, Any]] = []
    for directory in sorted(p for p in root.rglob("*") if p.is_dir() and not _is_external_noise(p)):
        rel = directory.relative_to(root).as_posix()
        files = {p.name for p in directory.iterdir() if p.is_file()}
        py_files = sorted(p.name for p in directory.glob("*.py"))
        if not ((files & markers) or py_files):
            continue
        category = rel.split("/")[0]
        launchers = _detect_launchers(directory)
        item = {
            "id": _slug(rel),
            "name": directory.name,
            "title": _read_title(directory),
            "path": rel,
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, category.replace("_", " ").title()),
            "type": "node" if (directory / "package.json").exists() and not py_files else "python" if py_files else "skill" if category == "agent_skills" else "project",
            "has_readme": any((directory / name).exists() for name in ("README.md", "readme.md")),
            "has_requirements": (directory / "requirements.txt").exists(),
            "has_package_json": (directory / "package.json").exists(),
            "has_pyproject": (directory / "pyproject.toml").exists(),
            "python_files": py_files,
            "entrypoints": _python_entrypoints(directory),
            "launchers": launchers,
            "requires_setup": bool((directory / "requirements.txt").exists() or (directory / "package.json").exists() or (directory / "pyproject.toml").exists()),
        }
        items.append(item)
    return items


def _catalog_by_id_or_path(identifier: str) -> dict[str, Any]:
    matches = [item for item in discover_catalog() if item["id"] == identifier or item["path"] == identifier or item["name"] == identifier]
    if not matches:
        raise KeyError(f"No awesome-llm-apps template found for {identifier!r}")
    if len(matches) > 1:
        exact = [item for item in matches if item["id"] == identifier or item["path"] == identifier]
        if len(exact) == 1:
            return exact[0]
        raise KeyError(f"Ambiguous template {identifier!r}; use one of: {[m['path'] for m in matches[:10]]}")
    return matches[0]


def status() -> dict[str, Any]:
    src = source_dir()
    catalog = discover_catalog()
    categories: dict[str, int] = {}
    for item in catalog:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
    return {
        "integration": "awesome-llm-apps",
        "remote": REMOTE,
        "pinned_commit": PINNED_COMMIT,
        "source_dir": str(src),
        "source_exists": src.exists(),
        "source_commit": _git_value(["rev-parse", "HEAD"], src) if src.exists() else None,
        "source_branch": _git_value(["branch", "--show-current"], src) if src.exists() else None,
        "home": str(integration_home()),
        "template_count": len(catalog),
        "categories": dict(sorted(categories.items())),
        "python": shutil.which("python3") or sys.executable,
        "node": shutil.which("node"),
        "npm": shutil.which("npm"),
        "streamlit": shutil.which("streamlit"),
    }


def doctor() -> dict[str, Any]:
    info = status()
    issues: list[str] = []
    warnings: list[str] = []
    if not info["source_exists"]:
        issues.append("Source submodule is missing; run `git submodule update --init --recursive integrations/awesome-llm-apps`.")
    elif info["source_commit"] != PINNED_COMMIT:
        warnings.append(f"Source is at {info['source_commit']}, expected pinned commit {PINNED_COMMIT}.")
    if info["template_count"] == 0 and info["source_exists"]:
        issues.append("Source exists but no app/agent templates were discovered.")
    if not info["node"] or not info["npm"]:
        warnings.append("Node/npm not found; Node-based generative UI templates cannot be setup/run until installed.")
    if not info["streamlit"]:
        warnings.append("streamlit not found on PATH; Streamlit templates need per-template setup before launch.")
    return {"ok": not issues, "status": info, "issues": issues, "warnings": warnings}


def list_templates(category: str | None = None, query: str | None = None, limit: int = 50) -> dict[str, Any]:
    items = discover_catalog()
    if category:
        items = [item for item in items if item["category"] == category]
    if query:
        q = query.lower()
        items = [item for item in items if q in item["path"].lower() or q in item["name"].lower() or q in (item.get("title") or "").lower()]
    return {"ok": True, "count": len(items), "templates": items[:limit]}


def show(identifier: str) -> dict[str, Any]:
    item = _catalog_by_id_or_path(identifier)
    directory = source_dir() / item["path"]
    readme_path = next((directory / name for name in ("README.md", "readme.md") if (directory / name).exists()), None)
    readme = None
    if readme_path:
        text = readme_path.read_text(errors="ignore")
        readme = text[:8000]
    return {"ok": True, "template": item, "readme": readme}


def template_env_dir(item: dict[str, Any]) -> Path:
    return integration_home() / "envs" / item["id"]


def setup(identifier: str, timeout: int = 900, node: bool = True, python: bool = True) -> dict[str, Any]:
    item = _catalog_by_id_or_path(identifier)
    directory = source_dir() / item["path"]
    env_dir = template_env_dir(item)
    env_dir.mkdir(parents=True, exist_ok=True)
    steps: list[dict[str, Any]] = []

    if python and item["has_requirements"]:
        venv = env_dir / "venv"
        if not venv.exists():
            steps.append(_run_capture([sys.executable, "-m", "venv", str(venv)], timeout=120))
        pip = venv / "bin" / "pip"
        steps.append(_run_capture([str(pip), "install", "-r", str(directory / "requirements.txt")], cwd=directory, timeout=timeout))
    elif python and item["has_pyproject"]:
        venv = env_dir / "venv"
        if not venv.exists():
            steps.append(_run_capture([sys.executable, "-m", "venv", str(venv)], timeout=120))
        pip = venv / "bin" / "pip"
        steps.append(_run_capture([str(pip), "install", "-e", str(directory)], cwd=directory, timeout=timeout))

    if node and item["has_package_json"]:
        if shutil.which("npm"):
            steps.append(_run_capture(["npm", "install"], cwd=directory, timeout=timeout))
        else:
            steps.append({"ok": False, "returncode": 127, "stdout": "", "stderr": "npm is not installed"})

    ok = all(step.get("ok", False) for step in steps) if steps else True
    return {"ok": ok, "template": item, "env_dir": str(env_dir), "steps": steps}


def _runner_env(item: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("OLLAMA_HOST", "http://192.168.1.111:11434")
    env.setdefault("OPENAI_BASE_URL", "http://192.168.1.111:11434/v1")
    env.setdefault("OPENAI_MODEL", "qwen2.5:14b")
    env_dir = template_env_dir(item)
    python_bin = env_dir / "venv" / "bin" / "python"
    if python_bin.exists():
        env["PATH"] = f"{python_bin.parent}:{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(env_dir / "venv")
    return env


def run_template(identifier: str, launcher: str | None = None, args: Iterable[str] = (), timeout: int = 300) -> dict[str, Any]:
    item = _catalog_by_id_or_path(identifier)
    directory = source_dir() / item["path"]
    launchers = item.get("launchers") or {}
    launcher_name = launcher or ("streamlit" if "streamlit" in launchers else "python" if "python" in launchers else "node" if "node" in launchers else None)
    if not launcher_name or launcher_name not in launchers:
        return {"ok": False, "error": f"No launcher {launcher_name!r} for template", "template": item}
    command = [*launchers[launcher_name], *list(args)]
    if launcher_name == "python":
        env_dir = template_env_dir(item)
        python_bin = env_dir / "venv" / "bin" / "python"
        if python_bin.exists():
            command[0] = str(python_bin)
    result = _run_capture(command, cwd=directory, timeout=timeout, env=_runner_env(item))
    result["template"] = item
    result["launcher"] = launcher_name
    result["cmd"] = command
    return result


def emit(data: dict[str, Any]) -> int:
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0 if data.get("ok", True) else 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage the awesome-llm-apps external template collection.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("doctor")

    list_p = sub.add_parser("list")
    list_p.add_argument("--category")
    list_p.add_argument("--query")
    list_p.add_argument("--limit", type=int, default=50)

    show_p = sub.add_parser("show")
    show_p.add_argument("template")

    setup_p = sub.add_parser("setup")
    setup_p.add_argument("template")
    setup_p.add_argument("--timeout", type=int, default=900)
    setup_p.add_argument("--no-node", action="store_true")
    setup_p.add_argument("--no-python", action="store_true")

    run_p = sub.add_parser("run")
    run_p.add_argument("template")
    run_p.add_argument("--launcher", choices=["python", "streamlit", "node"])
    run_p.add_argument("--timeout", type=int, default=300)
    run_p.add_argument("args", nargs=argparse.REMAINDER)

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "status":
        return emit(status())
    if args.command == "doctor":
        return emit(doctor())
    if args.command == "list":
        return emit(list_templates(category=args.category, query=args.query, limit=args.limit))
    if args.command == "show":
        return emit(show(args.template))
    if args.command == "setup":
        return emit(setup(args.template, timeout=args.timeout, node=not args.no_node, python=not args.no_python))
    if args.command == "run":
        return emit(run_template(args.template, launcher=args.launcher, args=args.args, timeout=args.timeout))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
