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
```

All agents follow the MCP pattern and can be extended with real LLM/tool calls.

OpenCRABS is integrated as a git submodule plus process boundary. See
`integrations/README.md` for setup, build, and runtime details.