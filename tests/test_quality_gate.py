from __future__ import annotations

import json
from pathlib import Path

from scripts import quality_gate


def test_issue_marker_scan_excludes_external_roots_and_catches_first_party(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    first_party = root / "scripts" / "bad.py"
    first_party.parent.mkdir()
    marker = "TO" + "DO"
    first_party.write_text(f"# {marker}: fix this\n")
    external = root / "integrations" / "momo" / "ignored.py"
    external.parent.mkdir(parents=True)
    external.write_text(f"# {marker}: upstream marker\n")

    monkeypatch.setattr(quality_gate, "ROOT", root)

    matches = quality_gate.scan_issue_markers(root)

    assert len(matches) == 1
    assert matches[0].startswith("scripts/bad.py:1")


def test_quality_gate_writes_structured_report(tmp_path: Path) -> None:
    report = quality_gate.QualityGateReport(
        ok=True,
        started_at_unix=1.0,
        duration_seconds=0.5,
        results=[quality_gate.GateResult(name="example", ok=True, duration_seconds=0.1)],
    )

    output = quality_gate.write_report(report, tmp_path / "quality.json")
    data = json.loads(output.read_text())

    assert data["ok"] is True
    assert data["results"][0]["name"] == "example"


def test_quality_gate_lists_core_checks(capsys) -> None:
    assert quality_gate.main(["--list-checks"]) == 0
    output = capsys.readouterr().out

    assert "ruff" in output
    assert "mypy" in output
    assert "run-tests" in output
    assert "safety-policy" in output
    assert "cron-state" in output
