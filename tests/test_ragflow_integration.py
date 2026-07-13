from __future__ import annotations

from agents.dispatcher import AGENT_REGISTRY, HermesDispatcher
from agents.ragflow_agent import RAGFlowAgent
from scripts import ragflow_manage


def test_ragflow_status_reports_pinned_source():
    result = ragflow_manage.status()

    assert result["ok"] is True
    assert result["integration"] == "ragflow"
    assert result["product_name"] == "RAGFlow"
    assert result["source_exists"] is True
    assert result["source_commit"] == ragflow_manage.PINNED_COMMIT
    assert result["remote"] == ragflow_manage.REMOTE
    assert result["version"] == "0.26.4"
    assert result["required_files_missing"] == []


def test_ragflow_doctor_is_actionable_without_running_stack():
    result = ragflow_manage.doctor()

    assert result["ok"] is True
    assert isinstance(result["issues"], list)
    assert isinstance(result["warnings"], list)
    assert all("source submodule is missing" not in issue for issue in result["issues"])
    assert any("16GB RAM" in warning for warning in result["warnings"])


def test_ragflow_render_config_uses_hermes_runtime(monkeypatch, tmp_path):
    home = tmp_path / "ragflow-home"
    runtime = home / "docker"
    monkeypatch.setattr(ragflow_manage, "HOME", home)
    monkeypatch.setattr(ragflow_manage, "RUNTIME_DOCKER_DIR", runtime)
    monkeypatch.setattr(ragflow_manage, "COMPOSE_FILE", runtime / "docker-compose.yml")
    monkeypatch.setattr(ragflow_manage, "BASE_COMPOSE_FILE", runtime / "docker-compose-base.yml")
    monkeypatch.setattr(ragflow_manage, "ENV_FILE", runtime / ".env")

    result = ragflow_manage.render_config()
    env_text = (runtime / ".env").read_text()

    assert result["ok"] is True
    assert (runtime / "docker-compose.yml").exists()
    assert (runtime / "docker-compose-base.yml").exists()
    assert "SVR_WEB_HTTP_PORT=8088" in env_text
    assert "SVR_HTTP_PORT=9380" in env_text
    assert "MYSQL_PASSWORD=hermes-ragflow-mysql-password" in env_text
    assert result["env_summary"]["key_count"] >= 50
    assert "MYSQL_PASSWORD" in result["env_summary"]["sensitive_keys"]


def test_ragflow_agent_status_and_unknown_task():
    agent = RAGFlowAgent()
    status = agent.execute("ragflow_status", {})
    unknown = agent.execute("does_not_exist", {})

    assert status["status"] == "completed"
    assert status["result"]["source_commit"] == ragflow_manage.PINNED_COMMIT
    assert unknown["status"] == "failed"
    assert "Unsupported RAGFlow task_type" in unknown["error"]


def test_dispatcher_knows_ragflow():
    assert "ragflow" in AGENT_REGISTRY
    assert "retrieval_augmented_generation" in AGENT_REGISTRY["ragflow"]
    assert HermesDispatcher().resolve_agent("ragflow_doctor") == "ragflow"
    assert HermesDispatcher().resolve_agent("retrieval_augmented_generation") == "ragflow"
