from __future__ import annotations


from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from agents.momo_agent import MomoAgent
from scripts import momo_manage


def test_momo_status_is_import_safe_without_rust(monkeypatch, tmp_path):
    monkeypatch.setenv("MOMO_SOURCE_DIR", str(tmp_path / "missing-momo"))
    monkeypatch.delenv("MOMO_BIN", raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("MOMO_BASE_URL", "http://127.0.0.1:9")

    result = momo_manage.status()

    assert result["integration"] == "momo"
    assert result["source_exists"] is False
    assert result["binary_available"] is False
    assert result["can_build"] is False
    assert result["service_healthy"] is False


def test_momo_doctor_reports_actionable_missing_source(monkeypatch, tmp_path):
    monkeypatch.setenv("MOMO_SOURCE_DIR", str(tmp_path / "missing-momo"))
    monkeypatch.delenv("MOMO_BIN", raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("MOMO_BASE_URL", "http://127.0.0.1:9")

    result = momo_manage.doctor()

    assert result["ok"] is False
    assert any("git submodule update" in issue for issue in result["issues"])
    assert any("Rust toolchain" in warning for warning in result["warnings"])
    assert any("not responding" in warning for warning in result["warnings"])


def test_momo_binary_can_be_supplied_by_env(monkeypatch, tmp_path):
    fake_bin = tmp_path / "momo"
    fake_bin.write_text("#!/bin/sh\necho momo fake\n")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("MOMO_BIN", str(fake_bin))

    assert momo_manage.find_momo_binary() == fake_bin.resolve()


def test_momo_agent_status_degrades_gracefully(monkeypatch, tmp_path):
    monkeypatch.setenv("MOMO_SOURCE_DIR", str(tmp_path / "missing-momo"))
    monkeypatch.delenv("MOMO_BIN", raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setenv("MOMO_BASE_URL", "http://127.0.0.1:9")

    result = MomoAgent().execute("status", {})

    assert result["status"] == "completed"
    assert result["action"] == "status"
    assert result["result"]["binary_available"] is False


def test_momo_agent_requires_query_for_search():
    result = MomoAgent().execute("search", {})

    assert result["status"] == "failed"
    assert "Missing query" in result["error"]


def test_momo_agent_requires_text_or_messages_for_ingest():
    result = MomoAgent().execute("ingest", {})

    assert result["status"] == "failed"
    assert "Missing text" in result["error"]


def test_momo_agent_requires_text_for_document():
    result = MomoAgent().execute("document", {})

    assert result["status"] == "failed"
    assert "Missing text" in result["error"]


def test_momo_service_env_uses_persistent_home(monkeypatch, tmp_path):
    monkeypatch.setenv("MOMO_HOME", str(tmp_path / "momo-home"))

    env = momo_manage._service_env()

    assert env["DATABASE_URL"].startswith("file:")
    assert str(tmp_path / "momo-home") in env["DATABASE_URL"]
    assert env["MOMO_API_KEYS"]


def test_momo_serve_defaults_to_no_internal_timeout(monkeypatch):
    captured = {}

    def fake_run_momo(args, timeout):
        captured["args"] = list(args)
        captured["timeout"] = timeout
        return {"ok": True}

    monkeypatch.setattr(momo_manage, "run_momo", fake_run_momo)

    assert momo_manage.serve()["ok"] is True
    assert captured["timeout"] is None
    assert captured["args"] == ["--mode", "api", "--single-process"]


def test_momo_serve_cli_zero_timeout_disables_internal_timeout(monkeypatch):
    captured = {}

    def fake_serve(timeout=None, single_process=True):
        captured["timeout"] = timeout
        captured["single_process"] = single_process
        return {"ok": True}

    monkeypatch.setattr(momo_manage, "serve", fake_serve)

    assert momo_manage.main(["serve", "--timeout", "0"]) == 0
    assert captured == {"timeout": None, "single_process": True}


def test_dispatcher_knows_momo_capabilities():
    assert "momo" in AGENT_REGISTRY
    assert "mcp_memory_server" in AGENT_REGISTRY["momo"]
    assert "momo_document" in AGENT_REGISTRY["momo"]
    assert HermesDispatcher().resolve_agent("momo_doctor") == "momo"
    assert HermesDispatcher().resolve_agent("mcp_memory") == "momo"
