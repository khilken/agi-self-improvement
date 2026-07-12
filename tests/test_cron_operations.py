from __future__ import annotations

import json
from pathlib import Path

from scripts import verify_cron_state
from scripts.youtube_digest import get_youtube_service, is_noninteractive


def test_cron_audit_flags_unpinned_snapshot() -> None:
    jobs = [
        {
            "id": "job-1",
            "name": "drift risk",
            "no_agent": False,
            "provider": None,
            "model": None,
            "provider_snapshot": "old-provider",
            "model_snapshot": "old-model",
            "last_error": None,
        }
    ]

    issues = verify_cron_state.audit_jobs(jobs)

    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "spend-drift" in issues[0].message


def test_cron_audit_warns_for_external_manual_actions() -> None:
    jobs = [
        {
            "id": "youtube",
            "name": "YouTube",
            "no_agent": True,
            "last_error": "Script exited with code 1\nRuntimeError: YouTube OAuth token.json is missing or invalid.",
        },
        {
            "id": "obsidian",
            "name": "Obsidian",
            "no_agent": False,
            "provider": "openai-codex",
            "model": "gpt-5.5",
            "last_error": "cannot import name 'env_float' from 'utils'",
        },
    ]

    issues = verify_cron_state.audit_jobs(jobs)

    assert [issue.severity for issue in issues] == ["warning", "warning"]
    assert "OAuth" in issues[0].message
    assert "restart Hermes gateway" in issues[1].message


def test_cron_state_main_allows_warnings_without_strict(tmp_path: Path, capsys) -> None:
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "youtube",
                        "name": "YouTube",
                        "no_agent": True,
                        "last_error": "RuntimeError: YouTube OAuth token.json is missing or invalid.",
                    }
                ]
            }
        )
    )

    assert verify_cron_state.main(["--jobs-path", str(jobs_path)]) == 0
    assert verify_cron_state.main(["--jobs-path", str(jobs_path), "--strict"]) == 1
    assert "issues: 1" in capsys.readouterr().out


def test_youtube_digest_fails_fast_noninteractive_without_token(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "credentials.json").write_text("{}")
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    try:
        get_youtube_service(tmp_path)
    except RuntimeError as exc:
        assert "token.json is missing or invalid" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected missing-token RuntimeError")


def test_youtube_noninteractive_detects_cron_env(monkeypatch) -> None:
    monkeypatch.setenv("HERMES_CRON_JOB_ID", "job-1")
    assert is_noninteractive() is True
