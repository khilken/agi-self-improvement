# MCP - Multi-Agent Communication Protocol (Hermes)

**Version:** 0.1.0  
**Integrated into:** Hermes v1.1+

## Overview

MCP provides Hermes with a native, persistent, auditable, and git-friendly way to communicate with and orchestrate specialized sub-agents.

It is designed around the philosophy of **persistence-first** and **human-inspectable** systems (JSON message files on disk).

## Key Features

- Standardized `MCPMessage` envelope with rich metadata
- File-backed persistent queues (`mcp/queues/<agent_name>/`)
- High-level helpers: `delegate_task()`, `report_result()`, `share_memory()`, `propose_self_improvement()`
- Simple agent registry for capability discovery
- `BaseMCPAgent` class for quickly building new sub-agents
- Fully compatible with the Hermes main loop and self-improvement goals

## Directory Structure

```
mcp/
├── __init__.py
├── protocol.py          # Core implementation
├── README.md
├── registry.json        # Agent discovery (auto-managed)
└── queues/
    ├── hermes/          # Messages for main Hermes instance
    ├── researcher/      # Example sub-agent queues
    └── ...
```

## Quick Usage (inside Hermes or any agent)

```python
from mcp.protocol import MCPProtocol, MessageType, AgentRegistry

mcp = MCPProtocol(agent_name="hermes")

# Delegate work
msg = mcp.delegate_task(
    to_agent="researcher",
    task_description="Find and summarize the latest research on self-improving LLM agents",
    context={"focus_areas": ["multi-agent systems", "persistent memory", "tool use"]},
    priority=2
)

# Later, process results
for response in mcp.process_inbox():
    if response.message_type == MessageType.TASK_RESULT:
        print("Got result:", response.payload)
```

## Creating a New Sub-Agent

```python
from mcp.protocol import BaseMCPAgent, MCPProtocol, MessageType

class ResearcherAgent(BaseMCPAgent):
    def get_capabilities(self):
        return ["web_research", "paper_summarization", "trend_analysis"]

    def handle_task_request(self, msg):
        # Your logic here (call web tools, LLM, etc.)
        result = {"summary": "...", "sources": [...]}
        self.mcp.report_result(
            to_agent=msg.from_agent,
            correlation_id=msg.correlation_id,
            result=result
        )

# Run it
agent = ResearcherAgent(name="researcher")
agent.run_loop()
```

## Integration with Hermes Self-Improvement

Hermes treats MCP as a first-class citizen:
- Improving the protocol itself is a high-priority self-evolution task.
- Creating robust, specialized sub-agents accelerates parallel progress.
- Sub-agents can propose improvements back to Hermes via `SELF_IMPROVEMENT_PROPOSAL` messages.

All significant MCP interactions should be mirrored/summarized into the Obsidian vault under `Hermes/MCP_Interactions/`.

## Future Roadmap (Hermes will evolve this)

- Richer routing & pub/sub patterns
- Vector memory / RAG integration via MCP
- Distributed transport options (HTTP, Redis) while keeping file transport as the reliable default
- Cryptographic signing of high-stakes messages
- Built-in task scheduling and retry logic

---

*This protocol exists to help Hermes become a true self-sustaining personal AGI through effective division of cognitive labor.*