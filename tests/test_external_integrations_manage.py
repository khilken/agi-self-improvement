from __future__ import annotations

from scripts import external_integrations_manage


def test_external_integrations_status_reports_all_managed_sources():
    result = external_integrations_manage.status()

    assert result["integration_count"] == 7
    assert set(result["integrations"]) == {
        "opencrabs",
        "momo",
        "awesome-llm-apps",
        "prefect",
        "project-nomad",
        "background-agents",
        "ragflow",
    }
    assert result["ok"] is True
    assert all(result["source_ready"].values())


def test_external_integrations_doctor_aggregates_warnings_without_source_failures():
    result = external_integrations_manage.doctor()

    assert result["integration_count"] == 7
    assert isinstance(result["issues"], list)
    assert isinstance(result["warnings"], list)
    assert all("source submodule is missing" not in issue for issue in result["issues"])


def test_external_integrations_summary_is_operator_friendly():
    result = external_integrations_manage.summary()

    assert result["integration_count"] == 7
    assert "source_ready" in result
    assert "issues" in result
    assert "warnings" in result
    for name, info in result["integrations"].items():
        assert info["source_exists"] is True, name
        assert info["source_commit"] == info["pinned_commit"], name
