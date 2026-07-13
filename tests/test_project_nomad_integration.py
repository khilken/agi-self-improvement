from __future__ import annotations

from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from agents.project_nomad_agent import ProjectNomadAgent
from scripts import project_nomad_manage


def test_project_nomad_status_reports_pinned_source():
    result = project_nomad_manage.status()

    assert result["integration"] == "project-nomad"
    assert result["source_exists"] is True
    assert result["source_commit"] == project_nomad_manage.PINNED_COMMIT
    assert result["remote"] == project_nomad_manage.NOMAD_REMOTE
    assert result["admin_package_json_exists"] is True
    assert result["compose_template_exists"] is True


def test_project_nomad_doctor_is_actionable_without_running_server():
    result = project_nomad_manage.doctor()

    assert result["ok"] is True
    assert isinstance(result["issues"], list)
    assert isinstance(result["warnings"], list)
    assert all("source submodule is missing" not in issue for issue in result["issues"])


def test_project_nomad_render_compose_uses_hermes_home(monkeypatch, tmp_path):
    home = tmp_path / "nomad-home"
    compose = home / "docker-compose.yml"
    monkeypatch.setattr(project_nomad_manage, "HOME", home)
    monkeypatch.setattr(project_nomad_manage, "COMPOSE_PATH", compose)
    monkeypatch.setattr(project_nomad_manage, "STORAGE_DIR", home / "storage")
    monkeypatch.setattr(project_nomad_manage, "BASE_URL", "http://127.0.0.1:18080")

    result = project_nomad_manage.render_compose()
    text = compose.read_text()

    assert result["ok"] is True
    assert str(home / "storage") in text
    assert "/opt/project-nomad" not in text
    assert "APP_KEY=replaceme" not in text
    assert "URL=http://127.0.0.1:18080" in text


def test_project_nomad_agent_status_and_unknown_task():
    agent = ProjectNomadAgent()
    status = agent.execute("nomad_status", {})
    unknown = agent.execute("does_not_exist", {})

    assert status["status"] == "completed"
    assert status["result"]["source_commit"] == project_nomad_manage.PINNED_COMMIT
    assert unknown["status"] == "failed"
    assert "Unsupported Project Nomad task_type" in unknown["error"]


def test_dispatcher_knows_project_nomad():
    assert "project_nomad" in AGENT_REGISTRY
    assert "offline_knowledge_server" in AGENT_REGISTRY["project_nomad"]
    assert HermesDispatcher().resolve_agent("nomad_doctor") == "project_nomad"
    assert HermesDispatcher().resolve_agent("offline_knowledge_server") == "project_nomad"
