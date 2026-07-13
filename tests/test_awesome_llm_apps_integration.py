from __future__ import annotations

from agents.awesome_llm_apps_agent import AwesomeLLMAppsAgent
from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from scripts import awesome_llm_apps_manage


def test_awesome_llm_apps_status_discovers_catalog():
    result = awesome_llm_apps_manage.status()

    assert result["integration"] == "awesome-llm-apps"
    assert result["source_exists"] is True
    assert result["source_commit"] == awesome_llm_apps_manage.PINNED_COMMIT
    assert result["template_count"] >= 100
    assert "starter_ai_agents" in result["categories"]
    assert "rag_tutorials" in result["categories"]


def test_awesome_llm_apps_list_can_filter_rag():
    result = awesome_llm_apps_manage.list_templates(query="rag", limit=10)

    assert result["ok"] is True
    assert result["count"] > 0
    assert result["templates"]
    assert any("rag" in item["path"].lower() or "rag" in (item.get("title") or "").lower() for item in result["templates"])


def test_awesome_llm_apps_show_template_readme():
    result = awesome_llm_apps_manage.show("starter_ai_agents/ai_travel_agent")

    assert result["ok"] is True
    assert result["template"]["path"] == "starter_ai_agents/ai_travel_agent"
    assert result["template"]["has_requirements"] is True
    assert result["readme"]


def test_awesome_llm_apps_agent_status_and_list():
    agent = AwesomeLLMAppsAgent()
    status = agent.execute("awesome_llm_apps_status", {})
    listing = agent.execute("awesome_llm_apps_list", {"query": "mcp", "limit": 5})

    assert status["status"] == "completed"
    assert status["result"]["template_count"] >= 100
    assert listing["status"] == "completed"
    assert listing["result"]["templates"]


def test_awesome_llm_apps_agent_requires_template_for_show():
    result = AwesomeLLMAppsAgent().execute("show", {})

    assert result["status"] == "failed"
    assert "Missing template" in result["error"]


def test_dispatcher_knows_awesome_llm_apps():
    assert "awesome_llm_apps" in AGENT_REGISTRY
    assert "agent_template_catalog" in AGENT_REGISTRY["awesome_llm_apps"]
    assert HermesDispatcher().resolve_agent("awesome_llm_apps_list") == "awesome_llm_apps"
    assert HermesDispatcher().resolve_agent("agent_template") == "awesome_llm_apps"
