"""Tests for safety governance and memory consolidation."""

import json
import time

from agents.safety_governance_agent import SafetyGovernanceAgent
from tracing.memory_consolidation import consolidate_old_traces


def test_safety_governance_flags_sensitive_unrestricted_changes():
    agent = SafetyGovernanceAgent()
    result = agent.review("p1", {
        "type": "config_change",
        "title": "Allow all permissions forever",
        "description": "Disable approval and use token/secret credentials",
        "target_file": "config/system.yaml",
        "risk_level": "high",
    })
    assert result["recommendation"] == "human_review"
    assert result["overall_risk_score"] > 0.5
    assert result["flags"]


def test_safety_governance_allows_low_risk_test_change():
    agent = SafetyGovernanceAgent()
    result = agent.review("p2", {
        "type": "process_improvement",
        "title": "Add regression test",
        "description": "Read-only verification with rollback notes",
        "target_file": "tests/test_example.py",
        "risk_level": "low",
    })
    assert result["overall_risk_score"] < 0.4


def test_memory_consolidation_archives_old_traces(tmp_path):
    trace_dir = tmp_path / "traces"
    archive_dir = tmp_path / "archive"
    trace_dir.mkdir()

    old_ts = time.time() - 86400 * 40
    recent_ts = time.time()
    (trace_dir / "old.json").write_text(json.dumps({
        "trace_id": "old",
        "agent": "researcher",
        "task_type": "research",
        "start_time": old_ts,
        "evaluation_score": 0.8,
    }))
    (trace_dir / "recent.json").write_text(json.dumps({
        "trace_id": "recent",
        "agent": "coder",
        "task_type": "code",
        "start_time": recent_ts,
    }))

    report = consolidate_old_traces(days=30, trace_dir=str(trace_dir), archive_dir=str(archive_dir))
    assert report["files_archived"] == 1
    assert not (trace_dir / "old.json").exists()
    assert (trace_dir / "recent.json").exists()
    assert list(archive_dir.glob("*/old.json"))
    assert report["average_evaluation_score"] == 0.8
