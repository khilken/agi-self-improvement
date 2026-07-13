# External Runtime Integrations

Hermes integrates selected external projects as managed subsystems behind process, network, or CLI boundaries. This keeps Hermes' Python runtime stable while still making external capabilities available through MCP agents and manager scripts.

## Unified external integration checks

Use the aggregate manager after adding or updating external runtimes:

```bash
PYTHONPATH=. python scripts/external_integrations_manage.py status
PYTHONPATH=. python scripts/external_integrations_manage.py doctor
PYTHONPATH=. python scripts/external_integrations_manage.py summary
```

The aggregate manager verifies that every managed source submodule exists and is
at its pinned commit, then aggregates each integration's own non-mutating
`doctor` output. This is the quickest operator check for maximum integration
health across OpenCRABS, Momo, Awesome LLM Apps, Prefect, and Project N.O.M.A.D.

## Project N.O.M.A.D.

Hermes integrates [Crosstalk-Solutions/project-nomad](https://github.com/Crosstalk-Solutions/project-nomad) as a managed external offline-first knowledge and education server.

Project N.O.M.A.D. is a Docker/Node application, not a Python package. Hermes therefore keeps it behind explicit Docker, Node, and HTTP boundaries:

- Source is tracked as a git submodule at `integrations/project-nomad`.
- `scripts/project_nomad_manage.py` manages status, diagnostics, local compose rendering, Docker Compose validation, and explicit start/stop operations.
- `agents/project_nomad_agent.py` exposes Project Nomad operations through Hermes MCP routing.
- Local compose/runtime state defaults to `~/.hermes/project-nomad`.
- Hermes verification excludes the external Project Nomad source tree from compile/import/pytest sweeps.

Pinned upstream commit:

```text
6a4f02dd4626c64f38ac07e4740bc250ba13fea1
```

Setup/status:

```bash
git submodule update --init --recursive integrations/project-nomad
PYTHONPATH=. python scripts/project_nomad_manage.py status
PYTHONPATH=. python scripts/project_nomad_manage.py doctor
```

Render a Hermes-local Docker Compose file without running the upstream sudo installer:

```bash
PYTHONPATH=. python scripts/project_nomad_manage.py render-compose
PYTHONPATH=. python scripts/project_nomad_manage.py compose-config
```

Start/stop are explicit because Project Nomad can pull and run multiple containers and exposes an unauthenticated local Command Center by design:

```bash
PYTHONPATH=. python scripts/project_nomad_manage.py up --timeout 600
PYTHONPATH=. python scripts/project_nomad_manage.py wait-ready --timeout 120
PYTHONPATH=. python scripts/project_nomad_manage.py down
```

Default local URL:

```text
http://127.0.0.1:8080
```

Capabilities exposed to Hermes:

- `project_nomad`
- `offline_knowledge_server`
- `offline_media_archives_data`
- `offline_ai_server`
- `nomad_status`
- `nomad_doctor`
- `nomad_render_compose`
- `nomad_compose_config`
- `nomad_setup`
- `nomad_build`
- `nomad_up`
- `nomad_down`
- `nomad_wait_ready`

Safety notes:

- Hermes does not run Project Nomad's `install_nomad.sh` automatically because it requires sudo/root privileges and is designed for Debian-based hosts.
- The generated compose file is placed under `~/.hermes/project-nomad` and rewrites `/opt/project-nomad/*` host paths into Hermes-local state paths.
- Project Nomad intentionally has no built-in authentication; do not expose it directly to the internet.
- Do not commit generated compose files, databases, downloaded media archives, models, ZIM files, Docker volumes, or local runtime state.

## OpenCRABS

Hermes integrates [adolfousier/opencrabs](https://github.com/adolfousier/opencrabs) as a managed external Rust agent runtime.

### Integration model

OpenCRABS is a full Rust application, not a Python package. Hermes therefore keeps a clean runtime boundary:

- OpenCRABS source is tracked as a git submodule at `integrations/opencrabs`.
- Hermes Python code talks to OpenCRABS through `scripts/opencrabs_manage.py`.
- MCP routing is exposed through `agents/opencrabs_agent.py`.
- Hermes' Python dependencies are not polluted by OpenCRABS' Rust/Cargo dependency graph.
- OpenCRABS state remains in `~/.opencrabs` unless `OPENCRABS_HOME` is set.

Pinned upstream commit:

```text
024e0cc287205e96ff162bb7187c115341b7b592
```

### Setup and usage

```bash
git submodule update --init --recursive integrations/opencrabs
PYTHONPATH=. python scripts/opencrabs_manage.py status
PYTHONPATH=. python scripts/opencrabs_manage.py doctor
PYTHONPATH=. python scripts/opencrabs_manage.py build
PYTHONPATH=. python scripts/opencrabs_manage.py run "Summarize your current configuration" --timeout 300
PYTHONPATH=. python agents/opencrabs_agent.py
```

Capabilities exposed to Hermes:

- `opencrabs`
- `rust_agent_runtime`
- `a2a_gateway`
- `external_agent_runtime`
- `opencrabs_status`
- `opencrabs_doctor`
- `opencrabs_build`
- `opencrabs_run`

## Momo

Hermes integrates [momomemory/momo](https://github.com/momomemory/momo) as a managed external Rust AI memory service.

Momo provides:

- REST memory/document/search APIs
- streamable HTTP MCP endpoint at `/mcp`
- LibSQL-backed vector memory
- local embedding support through FastEmbed
- optional local/Ollama-backed LLM features

### Integration model

Momo is a standalone HTTP service, not a Python package. Hermes therefore keeps it behind a service boundary:

- Momo source is tracked as a git submodule at `integrations/momo`.
- Hermes Python code manages and talks to Momo through `scripts/momo_manage.py`.
- MCP routing is exposed through `agents/momo_agent.py`.
- Runtime data defaults to `~/.momo` unless `MOMO_HOME`/Momo env vars override it.
- The default Hermes port is `3333` to avoid collisions with Momo's documented `3000` default.
- The wrapper uses `MOMO_API_KEY` or `HERMES_MOMO_API_KEY` when set, otherwise a local dev key `hermes-dev-key` for local-only startup.

Pinned upstream commit:

```text
3f32cd6069fe1491659e6fbd76af717a167b6741
```

### Setup

Initialize the submodule after cloning Hermes:

```bash
git submodule update --init --recursive integrations/momo
```

Check integration state:

```bash
PYTHONPATH=. python scripts/momo_manage.py status
PYTHONPATH=. python scripts/momo_manage.py doctor
```

Build Momo on hosts with Rust installed:

```bash
PYTHONPATH=. python scripts/momo_manage.py build
```

If Momo is installed elsewhere, point Hermes at it:

```bash
export MOMO_BIN=/path/to/momo
PYTHONPATH=. python scripts/momo_manage.py doctor
```

### Running Momo through Hermes

Foreground service:

```bash
PYTHONPATH=. python scripts/momo_manage.py serve --timeout 3600
```

For a long-lived tracked server from Hermes tools, start it as a background process with the same command.

Health check:

```bash
PYTHONPATH=. python scripts/momo_manage.py health
```

Ingest text into Momo memory:

```bash
PYTHONPATH=. python scripts/momo_manage.py ingest "Kevin prefers production-grade autonomous agents" --container-tag hermes
```

Create and list stored documents:

```bash
PYTHONPATH=. python scripts/momo_manage.py document "Hermes stores this in Momo" --container-tag hermes --title "Hermes note"
PYTHONPATH=. python scripts/momo_manage.py documents --container-tag hermes
```

Search memory/documents:

```bash
PYTHONPATH=. python scripts/momo_manage.py search "Kevin preferences" --container-tag hermes
```

MCP agent loop:

```bash
PYTHONPATH=. python agents/momo_agent.py
```

Dispatcher examples:

```python
from agents.dispatcher import HermesDispatcher

d = HermesDispatcher()
d.dispatch("momo", "momo_status", {})
d.dispatch("momo", "momo_doctor", {})
d.dispatch("momo", "momo_document", {"content": "Important project note", "container_tag": "hermes"})
d.dispatch("momo", "momo_ingest", {"text": "Important project fact", "container_tag": "hermes"})
d.dispatch("momo", "momo_search", {"query": "project fact", "container_tags": ["hermes"]})
```

Capabilities exposed to Hermes:

- `momo`
- `ai_memory_system`
- `external_memory_service`
- `mcp_memory_server`
- `momo_status`
- `momo_doctor`
- `momo_build`
- `momo_health`
- `momo_document`
- `momo_documents`
- `momo_search`
- `momo_ingest`

## Safety notes

- Wrappers are import-safe when Rust or service binaries are missing.
- Status and doctor are non-mutating.
- Build and service actions are explicit.
- Runtime state belongs under user homes (`~/.opencrabs`, `~/.momo`) or explicitly configured state directories, not in the Hermes repository.
- Do not commit generated Cargo build output, runtime DB files, API keys, or local service state.
- Hermes verification excludes external Rust submodules from Python compile/import sweeps.

## Awesome LLM Apps

Hermes integrates [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) as a managed external cookbook of runnable LLM apps, AI agents, RAG examples, MCP agents, voice agents, generative UI projects, and agent skills.

This repository is a collection of many independent templates with different dependency stacks. Hermes therefore does **not** import all template code into the Hermes Python runtime. Instead:

- Source is tracked as a git submodule at `integrations/awesome-llm-apps`.
- `scripts/awesome_llm_apps_manage.py` discovers and manages every app-like template.
- `agents/awesome_llm_apps_agent.py` exposes the catalog through Hermes MCP routing.
- Per-template virtualenvs and runtime state live under `~/.hermes/awesome-llm-apps`.
- Hermes test/import sweeps exclude the external source tree.

Pinned upstream commit:

```text
426cfa66b5fd832090038c36e50a6aa1dab3119c
```

### Setup

Initialize the submodule after cloning Hermes:

```bash
git submodule update --init --recursive integrations/awesome-llm-apps
```

Check integration state:

```bash
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py status
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py doctor
```

List/search all discovered templates:

```bash
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py list --limit 20
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py list --category rag_tutorials --limit 20
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py list --query mcp --limit 20
```

Show one template's metadata and README excerpt:

```bash
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py show starter_ai_agents/ai_travel_agent
```

Set up one template in its own isolated environment:

```bash
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py setup starter_ai_agents/ai_travel_agent
```

Run one template explicitly:

```bash
PYTHONPATH=. python scripts/awesome_llm_apps_manage.py run starter_ai_agents/ai_travel_agent --launcher streamlit --timeout 3600
```

Dispatcher examples:

```python
from agents.dispatcher import HermesDispatcher

d = HermesDispatcher()
d.dispatch("awesome_llm_apps", "awesome_llm_apps_status", {})
d.dispatch("awesome_llm_apps", "awesome_llm_apps_list", {"query": "rag", "limit": 10})
d.dispatch("awesome_llm_apps", "awesome_llm_apps_show", {"template": "starter_ai_agents/ai_travel_agent"})
```

Capabilities exposed to Hermes:

- `awesome_llm_apps`
- `llm_app_templates`
- `agent_template_catalog`
- `awesome_llm_apps_status`
- `awesome_llm_apps_doctor`
- `awesome_llm_apps_list`
- `awesome_llm_apps_show`
- `awesome_llm_apps_setup`
- `awesome_llm_apps_run`

### Safety notes for template runs

- Setup/run is per-template and explicit; Hermes does not install all template requirements globally.
- Many upstream templates require API keys, local files, browser automation, or UI ports. Use `show` before `setup`/`run`.
- The wrapper defaults OpenAI-compatible local settings toward Kevin's LAN Ollama where templates honor `OPENAI_BASE_URL`/model environment variables, but individual templates may require their own configuration.
- Do not commit generated `.venv`, `node_modules`, data files, or copied secrets from templates.

## Prefect

Hermes integrates [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) as a managed external workflow orchestration runtime.

Prefect is a full Python orchestration framework with its own CLI, server, UI, tests, docs, and optional integrations. Hermes therefore keeps Prefect behind a process/environment boundary instead of importing Prefect into the Hermes host runtime.

- Source is tracked as a git submodule at `integrations/prefect`.
- `scripts/prefect_manage.py` manages status, setup, CLI calls, local flow smoke tests, and server startup.
- `agents/prefect_agent.py` exposes Prefect operations through Hermes MCP routing.
- Prefect's virtualenv, SQLite state, and runtime home live under `~/.hermes/prefect`.
- Hermes verification excludes the external Prefect source tree from compile/import/pytest sweeps.

Pinned upstream commit:

```text
0e7435055e18952aa8604dab78507b087a18defb
```

### Setup

Initialize the source submodule after cloning Hermes:

```bash
git submodule update --init --recursive integrations/prefect
```

Inspect integration state:

```bash
PYTHONPATH=. python scripts/prefect_manage.py status
PYTHONPATH=. python scripts/prefect_manage.py doctor
```

Create/update the isolated Prefect environment from the pinned source:

```bash
PYTHONPATH=. python scripts/prefect_manage.py setup --timeout 1200
```

Run a local no-server flow smoke test:

```bash
PYTHONPATH=. python scripts/prefect_manage.py smoke
```

Call the Prefect CLI through the isolated environment:

```bash
PYTHONPATH=. python scripts/prefect_manage.py cli -- --version
PYTHONPATH=. python scripts/prefect_manage.py cli -- profile ls
```

Start the self-hosted Prefect API/UI server:

```bash
PYTHONPATH=. python scripts/prefect_manage.py server --timeout 3600
```

Default local URLs:

```text
UI:  http://127.0.0.1:4200
API: http://127.0.0.1:4200/api
```

Dispatcher examples:

```python
from agents.dispatcher import HermesDispatcher

d = HermesDispatcher()
d.dispatch("prefect", "prefect_status", {})
d.dispatch("prefect", "prefect_setup", {"timeout": 1200})
d.dispatch("prefect", "prefect_smoke", {})
d.dispatch("prefect", "prefect_cli", {"args": ["--version"]})
```

Capabilities exposed to Hermes:

- `prefect`
- `workflow_orchestration`
- `flow_orchestration`
- `prefect_status`
- `prefect_doctor`
- `prefect_setup`
- `prefect_cli`
- `prefect_smoke`
- `prefect_server`
- `prefect_wait_ready`

### Safety notes for Prefect

- Prefect installation is isolated to `~/.hermes/prefect/venv`; do not install its dependency set into Hermes' `.venv`.
- Prefect runtime state defaults to `~/.hermes/prefect/runtime` and `~/.hermes/prefect/prefect.db`.
- Server startup is explicit; Hermes does not start a long-lived Prefect API/UI server just to import the agent.
- Use `prefect_manage.py smoke` for a local flow check that does not require a running server.
- Do not commit Prefect databases, virtualenvs, logs, or generated UI/build artifacts.
