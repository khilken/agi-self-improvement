from __future__ import annotations

from agents.background_agents_agent import BackgroundAgentsAgent
from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from scripts import background_agents_manage


def test_background_agents_status_reports_pinned_source():
    result = background_agents_manage.status()

    assert result["ok"] is True
    assert result["integration"] == "background-agents"
    assert result["product_name"] == "Open-Inspect"
    assert result["source_exists"] is True
    assert result["source_commit"] == background_agents_manage.PINNED_COMMIT
    assert result["remote"] == background_agents_manage.REMOTE
    assert result["package_name"] == "open-inspect"
    assert "packages/*" in result["workspaces"]
    assert result["required_files_missing"] == []


def test_background_agents_doctor_is_actionable_without_deployment():
    result = background_agents_manage.doctor()

    assert result["ok"] is True
    assert isinstance(result["issues"], list)
    assert isinstance(result["warnings"], list)
    assert all("source submodule is missing" not in issue for issue in result["issues"])
    assert any("single-tenant" in warning for warning in result["warnings"])


def test_background_agents_agent_status_and_unknown_task():
    agent = BackgroundAgentsAgent()
    status = agent.execute("background_agents_status", {})
    unknown = agent.execute("does_not_exist", {})

    assert status["status"] == "completed"
    assert status["result"]["source_commit"] == background_agents_manage.PINNED_COMMIT
    assert unknown["status"] == "failed"
    assert "Unsupported Background Agents task_type" in unknown["error"]


def test_dispatcher_knows_background_agents():
    assert "background_agents" in AGENT_REGISTRY
    assert "open_inspect" in AGENT_REGISTRY["background_agents"]
    assert HermesDispatcher().resolve_agent("background_agents_doctor") == "background_agents"
    assert HermesDispatcher().resolve_agent("open_inspect_status") == "background_agents"
