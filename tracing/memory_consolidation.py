"""
Long-term Memory Consolidation
==============================

Consolidates old trace JSON files into dated archive summaries. This keeps the
live trace directory small while preserving auditable aggregate data.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import json
import shutil


def _parse_timestamp(trace: dict[str, Any], fallback_path: Path) -> datetime:
    value = trace.get("end_time") or trace.get("start_time")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    created = trace.get("created_at") or trace.get("timestamp")
    if isinstance(created, str):
        try:
            return datetime.fromisoformat(created)
        except ValueError:
            pass
    return datetime.fromtimestamp(fallback_path.stat().st_mtime)


def consolidate_old_traces(
    days: int = 30,
    trace_dir: str = "logs/traces",
    archive_dir: str = "logs/trace_archive",
    dry_run: bool = False,
) -> dict:
    """Archive traces older than ``days`` and write a summary JSON.

    Returns a structured report with counts and archive paths. Corrupt trace files
    are not deleted; they are reported under ``errors``.
    """
    trace_path = Path(trace_dir)
    archive_path = Path(archive_dir)
    archive_path.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now() - timedelta(days=days)

    candidates = []
    errors = []
    by_agent: Counter[str] = Counter()
    by_task_type: Counter[str] = Counter()
    scores = []

    for file_path in sorted(trace_path.glob("*.json")):
        try:
            data = json.loads(file_path.read_text())
            ts = _parse_timestamp(data, file_path)
        except Exception as exc:
            errors.append({"file": str(file_path), "error": str(exc)})
            continue

        if ts >= cutoff:
            continue

        candidates.append((file_path, data, ts))
        by_agent[str(data.get("agent", "unknown"))] += 1
        by_task_type[str(data.get("task_type", "unknown"))] += 1
        score = data.get("evaluation_score")
        if isinstance(score, (int, float)):
            scores.append(float(score))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_archive_dir = archive_path / f"traces_before_{cutoff.date()}_{stamp}"
    summary = {
        "created_at": datetime.now().isoformat(),
        "cutoff": cutoff.isoformat(),
        "dry_run": dry_run,
        "trace_dir": str(trace_path),
        "archive_dir": str(run_archive_dir),
        "files_considered": len(list(trace_path.glob("*.json"))) if trace_path.exists() else 0,
        "files_archived": len(candidates),
        "by_agent": dict(by_agent),
        "by_task_type": dict(by_task_type),
        "average_evaluation_score": round(sum(scores) / len(scores), 4) if scores else None,
        "errors": errors,
    }

    if not dry_run and candidates:
        run_archive_dir.mkdir(parents=True, exist_ok=True)
        for file_path, _data, _ts in candidates:
            shutil.move(str(file_path), str(run_archive_dir / file_path.name))
        (run_archive_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    elif dry_run:
        summary["would_archive"] = [str(path) for path, _data, _ts in candidates]

    return summary


if __name__ == "__main__":
    report = consolidate_old_traces()
    print(json.dumps(report, indent=2))
