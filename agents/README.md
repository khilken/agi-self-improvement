# Hermes Sub-Agents

This directory contains specialized sub-agents that Hermes can spawn and orchestrate via the **MCP (Multi-Agent Communication Protocol)**.

## Current Sub-Agents

### MemorySynthesizer (`memory_synthesizer.py`)

**Purpose:** Maintains and improves the long-term Vector Memory.

**Capabilities:**
- Memory consolidation and deduplication
- Creation of higher-level synthesized insights
- Importance scoring
- Periodic reflection generation
- Memory health reporting

**How Hermes uses it:**
Hermes delegates tasks using MCP with different `task_type` values (see Section 2.7 of the main System Prompt).

**Integration:**
- Communicates exclusively via MCP
- Reads from and writes to the shared `VectorMemory`
- Can propose improvements to the memory system

## Design Principles for Future Sub-Agents

All sub-agents in this directory should:
1. Inherit from `mcp.protocol.BaseMCPAgent`
2. Register useful capabilities
3. Handle `TASK_REQUEST` messages (and optionally others)
4. Use `VectorMemory` when they need long-term knowledge
5. Report results back via MCP
6. Be able to propose self-improvements when relevant

## Running a Sub-Agent

```bash
python agents/memory_synthesizer.py
```

In production, Hermes (or a supervisor process) will manage starting, monitoring, and communicating with these agents.

---

*Sub-agents are the key to scaling Hermes' cognitive capacity toward true self-sustaining AGI.*