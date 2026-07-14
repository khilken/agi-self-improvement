from __future__ import annotations


from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from agents.opencrabs_agent import OpenCrabsAgent
from scripts import opencrabs_manage


def test_opencrabs_status_is_import_safe_without_rust(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCRABS_SOURCE_DIR", str(tmp_path / "missing-opencrabs"))
    monkeypatch.delenv("OPENCRABS_BIN", raising=False)
    monkeypatch.setenv("PATH", "")

    result = opencrabs_manage.status()

    assert result["integration"] == "opencrabs"
    assert result["source_exists"] is False
    assert result["binary_available"] is False
    assert result["can_build"] is False


def test_opencrabs_doctor_reports_actionable_missing_source(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCRABS_SOURCE_DIR", str(tmp_path / "missing-opencrabs"))
    monkeypatch.delenv("OPENCRABS_BIN", raising=False)
    monkeypatch.setenv("PATH", "")

    result = opencrabs_manage.doctor()

    assert result["ok"] is False
    assert any("git submodule update" in issue for issue in result["issues"])
    assert any("Rust toolchain" in warning for warning in result["warnings"])


def test_opencrabs_binary_can_be_supplied_by_env(monkeypatch, tmp_path):
    fake_bin = tmp_path / "opencrabs"
    fake_bin.write_text("#!/bin/sh\necho opencrabs fake\n")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("OPENCRABS_BIN", str(fake_bin))

    assert opencrabs_manage.find_opencrabs_binary() == fake_bin.resolve()


def test_opencrabs_agent_status_degrades_gracefully(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCRABS_SOURCE_DIR", str(tmp_path / "missing-opencrabs"))
    monkeypatch.delenv("OPENCRABS_BIN", raising=False)
    monkeypatch.setenv("PATH", "")

    result = OpenCrabsAgent().execute("status", {})

    assert result["status"] == "completed"
    assert result["action"] == "status"
    assert result["result"]["binary_available"] is False


def test_opencrabs_agent_requires_prompt_for_run():
    result = OpenCrabsAgent().execute("run", {})

    assert result["status"] == "failed"
    assert "Missing prompt" in result["error"]


def test_dispatcher_knows_opencrabs_capabilities():
    assert "opencrabs" in AGENT_REGISTRY
    assert "a2a_gateway" in AGENT_REGISTRY["opencrabs"]
    assert HermesDispatcher().resolve_agent("opencrabs_doctor") == "opencrabs"
    assert HermesDispatcher().resolve_agent("a2a_gateway") == "opencrabs"
