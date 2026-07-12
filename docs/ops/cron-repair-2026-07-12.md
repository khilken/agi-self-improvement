# Hermes Autonomous Cron Repair Snapshot — 2026-07-12

This snapshot records the operational cron repair performed from the Hermes self project session. It intentionally excludes secrets, OAuth tokens, API keys, full prompts, and private output payloads.

## Live state changed outside this repo

- Backed up the live cron store to `~/.hermes/cron/jobs.json.bak-20260712-115044`.
- Pinned 15 agent-backed cron jobs to the current explicit provider/model:
  - provider: `openai-codex`
  - model: `gpt-5.5`
- Verified no unpinned jobs retain `provider_snapshot` / `model_snapshot` values that would trigger Hermes' spend-drift guard.
- Patched `~/.hermes/scripts/youtube_digest.py` so missing/invalid `token.json` fails fast in non-interactive cron instead of hanging until the 120s script timeout.
- Diagnosed `obsidian-health-check` `env_float` import failure as stale gateway process state: `utils.env_float` exists on disk and imports successfully in the current Hermes install.

## Sanitized cron summary

| Count | State |
|---:|---|
| 17 | total active jobs |
| 15 | agent-backed jobs pinned to `openai-codex` / `gpt-5.5` |
| 1 | script-only no-agent YouTube digest job |
| 0 | unpinned jobs with provider/model snapshots remaining |

Representative repaired jobs verified with a mocked scheduler run, avoiding inference/spend:

```text
ee607e0e7eac success True agent_constructed True error None
d202a47f9e0d success True agent_constructed True error None
3d1c9a716c5f success True agent_constructed True error None
1d2f7812ab72 success True agent_constructed True error None
```

## YouTube digest status

The job no longer times out. It now exits quickly with an actionable setup error because `~/.hermes/scripts/token.json` is missing or invalid.

To finish setup, run once from a real interactive terminal and complete the Google OAuth browser flow:

```bash
/Users/kevin/.hermes/hermes-agent/venv/bin/python /Users/kevin/.hermes/scripts/youtube_digest.py
```

This should create `~/.hermes/scripts/token.json`. Do not commit that token.

## Obsidian health-check status

The previous error:

```text
cannot import name 'env_float' from 'utils'
```

is stale gateway process state. Verified current install has `utils.env_float` available.

Required external action:

```bash
hermes gateway restart
# or
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
```

Hermes blocks gateway restart from inside a gateway-spawned session because the command would be killed mid-flight.

## Notes

- `hermes cron list` may keep showing old `last_run` drift errors until each job fires again. The underlying records are repaired.
- `~/.hermes/cron/jobs.json` and OAuth files are operational state and should not be committed to this project repo.
