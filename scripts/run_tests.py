#!/usr/bin/env python3
"""Hermes project verification runner.

Runs deterministic local checks and returns a failing exit code if any required
check fails. This intentionally avoids fake "all passed" output.
"""

from __future__ import annotations

import argparse
import os
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "logs"}
SKIP_PREFIXES = {
    (Path("integrations") / "opencrabs").parts,
    (Path("integrations") / "momo").parts,
    (Path("integrations") / "awesome-llm-apps").parts,
    (Path("integrations") / "prefect").parts,
}


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    if any(part in SKIP_DIRS for part in rel_parts):
        return True
    return any(rel_parts[: len(prefix)] == prefix for prefix in SKIP_PREFIXES)


def iter_python_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*.py")):
        if should_skip(path):
            continue
        yield path


def compile_check() -> tuple[bool, list[str]]:
    failures: list[str] = []
    checked = 0
    for path in iter_python_files():
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
    return not failures, [f"compiled {checked} Python files", *failures]


def import_check() -> tuple[bool, list[str]]:
    script = r'''
import pathlib, sys
root = pathlib.Path('.')
fail=[]; ok=0
skip_prefixes = {('integrations', 'opencrabs'), ('integrations', 'momo'), ('integrations', 'awesome-llm-apps'), ('integrations', 'prefect')}
for p in sorted(root.rglob('*.py')):
    if any(part in {'.git','__pycache__','.venv','venv','logs'} for part in p.parts):
        continue
    if any(p.parts[:len(prefix)] == prefix for prefix in skip_prefixes):
        continue
    if p.name.startswith('_'):
        continue
    mod='.'.join(p.with_suffix('').parts)
    try:
        __import__(mod)
        ok += 1
    except SystemExit:
        ok += 1
    except Exception as e:
        fail.append(f"{mod}: {type(e).__name__}: {e}")
print(f"imported {ok} modules")
if fail:
    print("IMPORT FAILURES:")
    print("\n".join(fail))
    sys.exit(1)
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    lines = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode == 0, lines


def pytest_check() -> tuple[bool, list[str]]:
    ignore_args = [
        "--ignore=integrations/opencrabs",
        "--ignore=integrations/momo",
        "--ignore=integrations/awesome-llm-apps",
        "--ignore=integrations/prefect",
    ]
    commands = [
        [sys.executable, "-m", "pytest", "-q", *ignore_args],
        ["pytest", "-q", *ignore_args],
    ]
    last_output: list[str] = []
    for command in commands:
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=180,
                env={**os.environ, "PYTHONPATH": str(ROOT)},
            )
        except FileNotFoundError:
            last_output = [f"command not found: {command[0]}"]
            continue
        output = (result.stdout + result.stderr).strip().splitlines()
        if result.returncode == 0:
            return True, output or ["pytest passed"]
        last_output = output or [f"{' '.join(command)} failed with {result.returncode}"]
    return False, last_output


def run_tests(include_pytest: bool = True) -> bool:
    checks = [
        ("compile", compile_check),
        ("imports", import_check),
    ]
    if include_pytest:
        checks.append(("pytest", pytest_check))
    all_ok = True
    print("Running Hermes verification checks...")
    for name, fn in checks:
        ok, lines = fn()
        status = "PASS" if ok else "FAIL"
        print(f"\n[{status}] {name}")
        for line in lines[-20:]:
            print(f"  {line}")
        all_ok = all_ok and ok
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Hermes verification checks")
    parser.add_argument("--no-pytest", action="store_true", help="Skip pytest (useful inside tests to avoid recursion)")
    args = parser.parse_args()
    sys.exit(0 if run_tests(include_pytest=not args.no_pytest) else 1)
