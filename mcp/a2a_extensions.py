"""
A2A (Agent-to-Agent) Protocol Extensions for Hermes MCP
=======================================================

Adds A2A-style capabilities on top of the existing MCP:
- Agent Cards (capability advertisement)
- Task lifecycle states
- Structured inter-agent messaging

This makes Hermes compatible with emerging 2026 A2A standards.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import uuid


class TaskState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCard:
    """A2A-style Agent Card for capability discovery."""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    endpoint: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "endpoint": self.endpoint,
            "version": self.version,
            "metadata": self.metadata,
        }


class A2AProtocol:
    """Lightweight A2A extensions on top of MCP."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.agent_card = AgentCard(
            agent_id=str(uuid.uuid4()),
            name=agent_name,
            description=f"Hermes {agent_name} agent",
            capabilities=[],
        )
        self.known_agents: Dict[str, AgentCard] = {}

    def register_capabilities(self, capabilities: List[str]):
        self.agent_card.capabilities = capabilities

    def get_agent_card(self) -> AgentCard:
        return self.agent_card

    def discover_agent(self, agent_card: AgentCard):
        self.known_agents[agent_card.agent_id] = agent_card

    def create_task_message(
        self,
        to_agent: str,
        task_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an A2A-style task message."""
        return {
            "message_type": "task_request",
            "from": self.agent_name,
            "to": to_agent,
            "task_type": task_type,
            "payload": payload,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "state": TaskState.PENDING.value,
        }


# Global A2A instance
a2a = A2AProtocol("hermes")