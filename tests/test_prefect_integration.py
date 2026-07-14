from __future__ import annotations

from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from agents.prefect_agent import PrefectAgent
from scripts import prefect_manage


def test_prefect_status_reports_pinned_source():
    result = prefect_manage.status()

    assert result["integration"] == "prefect"
    assert result["source_exists"] is True
    assert result["source_commit"] == prefect_manage.PINNED_COMMIT
    assert result["remote"] == prefect_manage.PREFECT_REMOTE
    assert result["home"].endswith(".hermes/prefect")


def test_prefect_doctor_is_actionable_without_server():
    result = prefect_manage.doctor()

    assert result["ok"] is True
    assert "status" in result
    assert isinstance(result["warnings"], list)
    assert isinstance(result["issues"], list)


def test_prefect_agent_status_and_unknown_task():
    agent = PrefectAgent()
    status = agent.execute("prefect_status", {})
    unknown = agent.execute("does_not_exist", {})

    assert status["status"] == "completed"
    assert status["result"]["source_commit"] == prefect_manage.PINNED_COMMIT
    assert unknown["status"] == "failed"
    assert "Unsupported Prefect task_type" in unknown["error"]


def test_prefect_agent_smoke_requires_setup_if_uninitialized(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_PREFECT_HOME", str(tmp_path / "prefect-home"))
    monkeypatch.setenv("HERMES_PREFECT_VENV", str(tmp_path / "prefect-venv"))

    result = PrefectAgent().execute("prefect_smoke", {})

    assert result["status"] == "failed"
    assert "setup" in result["result"]["error"].lower()


def test_prefect_server_defaults_to_no_internal_timeout(monkeypatch, tmp_path):
    fake_cli = tmp_path / "venv" / "bin" / "prefect"
    fake_cli.parent.mkdir(parents=True)
    fake_cli.write_text("#!/bin/sh\n")
    captured = {}

    def fake_prefect_bin():
        return fake_cli

    def fake_run_capture(cmd, timeout, env):
        captured["cmd"] = list(cmd)
        captured["timeout"] = timeout
        captured["env"] = env
        return {"ok": True}

    monkeypatch.setattr(prefect_manage, "prefect_bin", fake_prefect_bin)
    monkeypatch.setattr(prefect_manage, "_run_capture", fake_run_capture)

    assert prefect_manage.server()["ok"] is True
    assert captured["timeout"] is None
    assert captured["cmd"][:3] == [str(fake_cli), "server", "start"]


def test_prefect_server_cli_zero_timeout_disables_internal_timeout(monkeypatch):
    captured = {}

    def fake_server(timeout=None):
        captured["timeout"] = timeout
        return {"ok": True}

    monkeypatch.setattr(prefect_manage, "server", fake_server)

    assert prefect_manage.main(["server", "--timeout", "0"]) == 0
    assert captured == {"timeout": None}


def test_dispatcher_knows_prefect():
    assert "prefect" in AGENT_REGISTRY
    assert "workflow_orchestration" in AGENT_REGISTRY["prefect"]
    assert HermesDispatcher().resolve_agent("prefect_smoke") == "prefect"
    assert HermesDispatcher().resolve_agent("workflow_orchestration") == "prefect"
