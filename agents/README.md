# Hermes Specialized Agents

This directory contains the growing family of specialized agents in the Hermes system.

## Core Agents

| Agent | File | Purpose |
|-------|------|---------|
| MemorySynthesizer | `memory_synthesizer.py` | Memory consolidation & clustering |
| Researcher | `researcher_agent.py` | Research & information synthesis |
| Coder | `coder_agent.py` | Code generation & development |
| Evaluator | `evaluator_agent.py` | Output evaluation & reflection |
| MetaImprover | `meta_improver_agent.py` | Self-improvement analysis |
| OpenCRABS | `opencrabs_agent.py` | Managed bridge to the external OpenCRABS Rust agent runtime |
| Momo | `momo_agent.py` | Managed bridge to the external Momo Rust AI memory service |
| AwesomeLLMApps | `awesome_llm_apps_agent.py` | Catalog/launcher for the external awesome-llm-apps template collection |
| Prefect | `prefect_agent.py` | Managed bridge to external Prefect workflow orchestration runtime |

## Supporting Modules

- `dispatcher.py` — Routes tasks to the correct agent
- `tracing/task_trace.py` — Structured task logging for analysis and improvement loops
- `mcp/a2a_extensions.py` — A2A protocol compatibility layer

## Usage

```python
from agents.dispatcher import HermesDispatcher

d = HermesDispatcher()

# Send work to different agents
d.dispatch("researcher", "research", {"query": "AGI self-improvement 2026"})
d.dispatch("evaluator", "evaluate", {"output": {...}, "trace_id": "xxx"})
d.dispatch("meta_improver", "analyze_traces", {})
d.dispatch("opencrabs", "opencrabs_doctor", {})
d.dispatch("momo", "momo_doctor", {})
d.dispatch("awesome_llm_apps", "awesome_llm_apps_list", {"query": "rag", "limit": 10})
d.dispatch("prefect", "prefect_smoke", {})
```

All agents follow the MCP pattern and can be extended with real LLM/tool calls.

OpenCRABS, Momo, Awesome LLM Apps, and Prefect are integrated as git submodules plus process boundaries. See
`integrations/README.md` for setup, build, and runtime details.