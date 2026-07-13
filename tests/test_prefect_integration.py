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


def test_dispatcher_knows_prefect():
    assert "prefect" in AGENT_REGISTRY
    assert "workflow_orchestration" in AGENT_REGISTRY["prefect"]
    assert HermesDispatcher().resolve_agent("prefect_smoke") == "prefect"
    assert HermesDispatcher().resolve_agent("workflow_orchestration") == "prefect"
