#!/usr/bin/env python3
"""Hermes local/CI quality gate.

This is the executable baseline for project health. It combines deterministic
source checks, tests, external-integration smoke status, cron-state audit, issue
marker scanning, and a small safety-governance policy smoke into one command.
It also emits structured JSON so autonomous agents can inspect failures without
scraping terminal prose.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOTS = {
    ("integrations", "opencrabs"),
    ("integrations", "momo"),
    ("integrations", "awesome-llm-apps"),
    ("integrations", "prefect"),
    ("integrations", "project-nomad"),
    ("integrations", "background-agents"),
    ("integrations", "ragflow"),
}
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "logs",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "target",
    "dist",
    "build",
}
_ISSUE_MARKERS = [
    "TO" + "DO",
    "FIX" + "ME",
    "BU" + "G",
    "HA" + "CK",
    "X" + "XX",
    "OPTI" + "MIZE",
    "place" + "holder",
    "Not" + "Implemented",
    "local" + "host:11434",
    "127" + r"\.0\.0\.1:11434",
]
ISSUE_MARKER_RE = re.compile("|".join(_ISSUE_MARKERS))
SOURCE_SUFFIXES = {".py", ".sh", ".md", ".toml", ".yaml", ".yml", ".json"}
SHELL_SCRIPTS = [
    "setup_hermes.sh",
    "start_hermes.sh",
    "soft_start_hermes.sh",
    "stop_hermes.sh",
]


@dataclass
class GateResult:
    name: str
    ok: bool
    duration_seconds: float
    skipped: bool = False
    details: list[str] = field(default_factory=list)


@dataclass
class QualityGateReport:
    ok: bool
    started_at_unix: float
    duration_seconds: float
    results: list[GateResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "started_at_unix": self.started_at_unix,
            "duration_seconds": self.duration_seconds,
            "results": [asdict(result) for result in self.results],
        }


def _is_external(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    parts = rel.parts
    return any(parts[: len(prefix)] == prefix for prefix in EXTERNAL_ROOTS)


def _should_skip_path(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    return any(part in SKIP_DIRS for part in rel.parts) or _is_external(path)


def _run_command(name: str, command: list[str], timeout: int = 300) -> GateResult:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
        )
    except FileNotFoundError as exc:
        return GateResult(name=name, ok=False, duration_seconds=time.time() - started, details=[str(exc)])
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr or ""
        return GateResult(
            name=name,
            ok=False,
            duration_seconds=time.time() - started,
            details=[*(stdout + stderr).strip().splitlines()[-20:], f"timed out after {timeout}s"],
        )

    output = (completed.stdout + completed.stderr).strip().splitlines()
    return GateResult(
        name=name,
        ok=completed.returncode == 0,
        duration_seconds=time.time() - started,
        details=output[-40:] or ["ok"],
    )


def scan_issue_markers(root: Path = ROOT) -> list[str]:
    matches: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if _should_skip_path(path):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if ISSUE_MARKER_RE.search(line):
                rel = path.relative_to(root)
                matches.append(f"{rel}:{line_no}: {line.strip()[:180]}")
    return matches


def issue_marker_check() -> GateResult:
    started = time.time()
    matches = scan_issue_markers()
    return GateResult(
        name="issue-markers",
        ok=not matches,
        duration_seconds=time.time() - started,
        details=[f"issue_marker_matches={len(matches)}", *matches[:40]],
    )


def shell_syntax_check() -> GateResult:
    existing = [script for script in SHELL_SCRIPTS if (ROOT / script).exists()]
    if not existing:
        return GateResult(name="shell-syntax", ok=True, skipped=True, duration_seconds=0.0, details=["no shell scripts configured"])
    return _run_command("shell-syntax", ["bash", "-n", *existing], timeout=60)


def safety_policy_check() -> GateResult:
    started = time.time()
    from agents.safety_governance_agent import SafetyGovernanceAgent

    agent = SafetyGovernanceAgent()
    high_risk = agent.review(
        "quality-gate-high-risk",
        {
            "type": "config_change",
            "title": "Bypass all approvals and expose secret token",
            "description": "Disable approval, use unrestricted network permissions, and write API keys.",
            "target_file": "config/system.yaml",
            "risk_level": "high",
        },
    )
    low_risk = agent.review(
        "quality-gate-low-risk",
        {
            "type": "process_improvement",
            "title": "Add regression test",
            "description": "Read-only verification with rollback notes.",
            "target_file": "tests/test_quality_gate.py",
            "risk_level": "low",
        },
    )
    ok = high_risk.get("recommendation") == "human_review" and low_risk.get("recommendation") == "auto_approve"
    return GateResult(
        name="safety-policy",
        ok=ok,
        duration_seconds=time.time() - started,
        details=[
            f"high_risk_recommendation={high_risk.get('recommendation')}",
            f"low_risk_recommendation={low_risk.get('recommendation')}",
        ],
    )


def external_summary_check() -> GateResult:
    return _run_command(
        "external-integrations",
        [sys.executable, "scripts/external_integrations_manage.py", "summary"],
        timeout=240,
    )


def cron_state_check(strict: bool = False) -> GateResult:
    jobs_path = Path.home() / ".hermes" / "cron" / "jobs.json"
    if not jobs_path.exists():
        return GateResult(
            name="cron-state",
            ok=True,
            skipped=True,
            duration_seconds=0.0,
            details=[f"cron jobs file not found: {jobs_path}"],
        )
    command = [sys.executable, "scripts/verify_cron_state.py"]
    if strict:
        command.append("--strict")
    return _run_command("cron-state", command, timeout=120)


def default_checks(strict_cron: bool = False) -> list[tuple[str, Any]]:
    ruff_command = ["ruff", "check", "."]
    for prefix in sorted(EXTERNAL_ROOTS):
        ruff_command.extend(["--exclude", "/".join(prefix)])
    mypy_command = [
        "mypy",
        "--explicit-package-bases",
        "--ignore-missing-imports",
        "--exclude",
        "integrations/(opencrabs|momo|awesome-llm-apps|prefect|project-nomad|background-agents|ragflow)",
        ".",
    ]
    return [
        ("ruff", lambda: _run_command("ruff", ruff_command, timeout=240)),
        ("mypy", lambda: _run_command("mypy", mypy_command, timeout=300)),
        ("run-tests", lambda: _run_command("run-tests", [sys.executable, "scripts/run_tests.py"], timeout=420)),
        ("shell-syntax", shell_syntax_check),
        ("issue-markers", issue_marker_check),
        ("safety-policy", safety_policy_check),
        ("external-integrations", external_summary_check),
        ("cron-state", lambda: cron_state_check(strict=strict_cron)),
    ]


def write_report(report: QualityGateReport, output: Path | None) -> Path:
    if output is None:
        output = ROOT / "logs" / "quality_gate" / "latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return output


def run_quality_gate(selected: set[str] | None = None, strict_cron: bool = False) -> QualityGateReport:
    started = time.time()
    results: list[GateResult] = []
    for name, check in default_checks(strict_cron=strict_cron):
        if selected is not None and name not in selected:
            continue
        result = check()
        results.append(result)
        status = "SKIP" if result.skipped else "PASS" if result.ok else "FAIL"
        print(f"[{status}] {result.name} ({result.duration_seconds:.2f}s)")
        for line in result.details[-8:]:
            print(f"  {line}")
    ok = all(result.ok for result in results)
    return QualityGateReport(ok=ok, started_at_unix=started, duration_seconds=time.time() - started, results=results)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Hermes quality gate")
    parser.add_argument("--only", action="append", choices=[name for name, _ in default_checks()], help="Run only the named check; may be repeated")
    parser.add_argument("--strict-cron", action="store_true", help="Fail cron-state on warnings as well as errors")
    parser.add_argument("--json-output", type=Path, default=None, help="Write structured report JSON to this path")
    parser.add_argument("--no-json-output", action="store_true", help="Do not write the default logs/quality_gate/latest.json report")
    parser.add_argument("--list-checks", action="store_true", help="List check names and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    check_names = [name for name, _ in default_checks()]
    if args.list_checks:
        print("\n".join(check_names))
        return 0
    selected = set(args.only) if args.only else None
    report = run_quality_gate(selected=selected, strict_cron=args.strict_cron)
    if not args.no_json_output:
        path = write_report(report, args.json_output)
        print(f"structured_report={path}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
