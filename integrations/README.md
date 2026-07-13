# OpenCRABS Integration

Hermes integrates [adolfousier/opencrabs](https://github.com/adolfousier/opencrabs) as a managed external Rust agent runtime.

## Integration model

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

## First-time setup

Initialize the submodule after cloning Hermes:

```bash
git submodule update --init --recursive integrations/opencrabs
```

Check integration state:

```bash
PYTHONPATH=. python scripts/opencrabs_manage.py status
PYTHONPATH=. python scripts/opencrabs_manage.py doctor
```

On hosts with Rust installed, build the OpenCRABS binary:

```bash
PYTHONPATH=. python scripts/opencrabs_manage.py build
```

This runs `cargo build --release` inside `integrations/opencrabs`.

If OpenCRABS is installed elsewhere, point Hermes at it instead:

```bash
export OPENCRABS_BIN=/path/to/opencrabs
PYTHONPATH=. python scripts/opencrabs_manage.py doctor
```

## Running OpenCRABS through Hermes

Non-interactive prompt:

```bash
PYTHONPATH=. python scripts/opencrabs_manage.py run "Summarize your current configuration" --timeout 300
```

Safe read-only OpenCRABS CLI commands:

```bash
PYTHONPATH=. python scripts/opencrabs_manage.py command status
PYTHONPATH=. python scripts/opencrabs_manage.py command doctor
PYTHONPATH=. python scripts/opencrabs_manage.py command version
```

MCP agent loop:

```bash
PYTHONPATH=. python agents/opencrabs_agent.py
```

Dispatcher examples:

```python
from agents.dispatcher import HermesDispatcher

d = HermesDispatcher()
d.dispatch("opencrabs", "opencrabs_status", {})
d.dispatch("opencrabs", "opencrabs_doctor", {})
d.dispatch("opencrabs", "opencrabs_run", {"prompt": "Audit this repo", "timeout": 300})
```

## Capabilities exposed to Hermes

`opencrabs` advertises:

- `opencrabs`
- `rust_agent_runtime`
- `a2a_gateway`
- `external_agent_runtime`
- `opencrabs_status`
- `opencrabs_doctor`
- `opencrabs_build`
- `opencrabs_run`

## Safety notes

- The wrapper is import-safe when Rust is missing.
- Build/run actions are explicit; status and doctor are non-mutating.
- `command` only allows a fixed safe read-only allowlist.
- OpenCRABS secrets should stay in `~/.opencrabs/keys.toml`, not in this repository.
- Do not commit generated OpenCRABS runtime state or Cargo build output.
