#!/usr/bin/env python3
"""Verify live Hermes cron state without making inference calls.

This is an audit helper for autonomous-operation reliability. It checks the live
Hermes cron job store for common operational regressions:

- provider/model snapshot drift guard state left on unpinned jobs
- agent-backed jobs that are neither pinned nor explicitly accepted as dynamic
- script-only jobs that timed out instead of failing with actionable errors

The script reads operational state only; it does not run jobs or call models.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_JOBS_PATH = Path.home() / ".hermes" / "cron" / "jobs.json"


@dataclass(frozen=True)
class CronIssue:
    job_id: str
    name: str
    severity: str
    message: str

    def format(self) -> str:
        return f"[{self.severity}] {self.job_id} {self.name}: {self.message}"


def _jobs_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        return payload["jobs"]
    if isinstance(payload, list):
        return payload
    raise ValueError("Unsupported cron jobs JSON shape; expected object with jobs[] or list")


def load_jobs(path: Path) -> list[dict[str, Any]]:
    return _jobs_from_payload(json.loads(path.read_text()))


def classify_last_error(error: str | None) -> str:
    text = error or ""
    if not text:
        return "none"
    if "global inference config drifted" in text:
        return "model/provider drift"
    if "token.json is missing" in text:
        return "youtube oauth missing"
    if "Script timed out" in text:
        return "script timeout"
    if "env_float" in text:
        return "stale gateway import"
    if text.startswith("Script exited"):
        return "script error"
    return "other"


def audit_jobs(jobs: list[dict[str, Any]]) -> list[CronIssue]:
    issues: list[CronIssue] = []
    for job in jobs:
        job_id = str(job.get("id") or "<missing-id>")
        name = str(job.get("name") or "<unnamed>")
        no_agent = bool(job.get("no_agent"))
        provider = job.get("provider")
        model = job.get("model")
        provider_snapshot = job.get("provider_snapshot")
        model_snapshot = job.get("model_snapshot")
        error_class = classify_last_error(job.get("last_error"))

        if not no_agent and (provider_snapshot or model_snapshot) and not (provider and model):
            issues.append(
                CronIssue(
                    job_id,
                    name,
                    "error",
                    "unpinned agent job still has provider/model snapshots and can trip spend-drift guard",
                )
            )
        if not no_agent and bool(provider) != bool(model):
            issues.append(
                CronIssue(job_id, name, "error", "provider/model pin is incomplete")
            )
        if no_agent and error_class == "script timeout":
            issues.append(
                CronIssue(job_id, name, "error", "script-only cron job timed out; make it bounded/noninteractive")
            )
        if error_class == "stale gateway import":
            issues.append(
                CronIssue(job_id, name, "warning", "last run saw stale gateway imports; restart Hermes gateway")
            )
        if error_class == "youtube oauth missing":
            issues.append(
                CronIssue(job_id, name, "warning", "YouTube OAuth token missing; complete browser consent once")
            )
    return issues


def summarize(jobs: list[dict[str, Any]], issues: list[CronIssue]) -> list[str]:
    pinned = sum(1 for job in jobs if job.get("provider") and job.get("model"))
    no_agent = sum(1 for job in jobs if job.get("no_agent"))
    snapshots_remaining = [
        str(job.get("id"))
        for job in jobs
        if not job.get("provider") and (job.get("provider_snapshot") or job.get("model_snapshot"))
    ]
    lines = [
        f"jobs: {len(jobs)}",
        f"pinned_agent_jobs: {pinned}",
        f"no_agent_jobs: {no_agent}",
        f"unpinned_jobs_with_snapshots: {snapshots_remaining}",
        f"issues: {len(issues)}",
    ]
    lines.extend(issue.format() for issue in issues)
    return lines


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit live Hermes cron state")
    parser.add_argument("--jobs-path", type=Path, default=DEFAULT_JOBS_PATH)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero for warnings as well as errors",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    jobs = load_jobs(args.jobs_path.expanduser())
    issues = audit_jobs(jobs)
    for line in summarize(jobs, issues):
        print(line)
    has_error = any(issue.severity == "error" for issue in issues)
    has_warning = any(issue.severity == "warning" for issue in issues)
    return 1 if has_error or (args.strict and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
