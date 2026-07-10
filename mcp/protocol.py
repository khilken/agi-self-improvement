"""
MCP - Multi-Agent Communication Protocol for Hermes
Version: 0.1.0 (Initial Implementation)
Purpose: Standardized, persistent, auditable communication layer between Hermes (main agent)
         and sub-agents. Enables task delegation, memory sharing, reflection, and self-evolution.

Design Goals:
- Simple, JSON-based, human-readable when possible
- Persistent by default (file-backed queues for reliability and git integration)
- Extensible message types
- Correlation IDs for tracking task chains
- Priority and TTL support
- Easy to integrate with Ollama-based agents and the Hermes main loop
"""

from __future__ import annotations
import json
import uuid
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import threading
import logging

logger = logging.getLogger("MCP")

# =============================================================================
# Message Types
# =============================================================================

class MessageType(str, Enum):
    # Core task lifecycle
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    TASK_UPDATE = "task_update"          # progress / intermediate status

    # Memory & Knowledge
    MEMORY_UPDATE = "memory_update"
    KNOWLEDGE_SHARE = "knowledge_share"

    # Meta / Self-improvement
    REFLECTION = "reflection"
    SELF_IMPROVEMENT_PROPOSAL = "self_improvement_proposal"
    CAPABILITY_UPDATE = "capability_update"

    # System / Control
    STATUS_REPORT = "status_report"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    SHUTDOWN = "shutdown"

    # Discovery & Registry
    AGENT_REGISTER = "agent_register"
    AGENT_DEREGISTER = "agent_deregister"
    AGENT_QUERY = "agent_query"


@dataclass
class MCPMessage:
    """Standard envelope for all MCP communication."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None          # links related messages (e.g. task chain)
    from_agent: str = "hermes"
    to_agent: str = "broadcast"                   # or specific agent name / "hermes"
    message_type: MessageType = MessageType.TASK_REQUEST
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: int = 5                             # 1=highest, 10=lowest
    ttl_seconds: Optional[int] = None             # time-to-live
    tags: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        data = json.loads(json_str)
        data["message_type"] = MessageType(data["message_type"])
        return cls(**data)

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.timestamp) > self.ttl_seconds


# =============================================================================
# File-based Persistent Transport (Simple, Reliable, Git-friendly)
# =============================================================================

class FileTransport:
    """
    Persistent message bus using the filesystem.
    Messages are stored as individual JSON files in queues/<agent_name>/ 
    This makes everything auditable, version-controllable, and survives restarts.
    """

    _instance = None

    def __new__(cls, base_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_path: Path = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        if base_path is None:
            import os
            base_path = Path.home() / ".hermes" / "mcp_queues"
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialized = True

    def _get_queue_dir(self, agent: str) -> Path:
        qdir = self.base_path / agent
        qdir.mkdir(exist_ok=True)
        return qdir

    def send(self, msg: MCPMessage) -> str:
        """Write message to the recipient's queue."""
        with self._lock:
            qdir = self._get_queue_dir(msg.to_agent)
            filename = f"{msg.timestamp:.6f}_{msg.message_id}.json"
            filepath = qdir / filename
            filepath.write_text(msg.to_json())
            logger.debug(f"MCP sent {msg.message_type} from {msg.from_agent} → {msg.to_agent}")
            return str(filepath)

    def receive(self, agent: str, delete_after_read: bool = True) -> List[MCPMessage]:
        """Read all pending messages for an agent (oldest first)."""
        qdir = self._get_queue_dir(agent)
        messages: List[MCPMessage] = []
        files = sorted(qdir.glob("*.json"))

        for f in files:
            try:
                content = f.read_text()
                msg = MCPMessage.from_json(content)
                if not msg.is_expired():
                    messages.append(msg)
                if delete_after_read:
                    f.unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"Failed to parse MCP message {f}: {e}")
                # Move bad file to errors/ for inspection
                error_dir = qdir / "errors"
                error_dir.mkdir(exist_ok=True)
                f.rename(error_dir / f.name)
        return messages

    def peek(self, agent: str, limit: int = 10) -> List[MCPMessage]:
        """Non-destructive read (for monitoring / debugging)."""
        qdir = self._get_queue_dir(agent)
        messages = []
        for f in sorted(qdir.glob("*.json"))[:limit]:
            try:
                messages.append(MCPMessage.from_json(f.read_text()))
            except Exception:
                pass
        return messages

    def clear_queue(self, agent: str):
        qdir = self._get_queue_dir(agent)
        for f in qdir.glob("*.json"):
            f.unlink(missing_ok=True)


# =============================================================================
# MCP Protocol Core
# =============================================================================

class MCPProtocol:
    """
    High-level protocol handler used by Hermes and sub-agents.
    Provides send/receive, task delegation helpers, and registry functions.
    """

    def __init__(self, agent_name: str, transport: Optional[FileTransport] = None):
        self.agent_name = agent_name
        self.transport = transport or FileTransport()
        self._handlers: Dict[MessageType, Callable[[MCPMessage], Optional[MCPMessage]]] = {}
        self.register_default_handlers()

    def register_handler(self, msg_type: MessageType, handler: Callable):
        self._handlers[msg_type] = handler

    def register_default_handlers(self):
        # Agents can override or extend these
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.ERROR, self._handle_error)

    def send(self, to_agent: str, msg_type: MessageType, payload: Dict[str, Any],
             correlation_id: Optional[str] = None, priority: int = 5,
             tags: Optional[List[str]] = None) -> MCPMessage:
        msg = MCPMessage(
            from_agent=self.agent_name,
            to_agent=to_agent,
            message_type=msg_type,
            payload=payload,
            correlation_id=correlation_id,
            priority=priority,
            tags=tags or []
        )
        self.transport.send(msg)
        return msg

    # Convenience alias used by Dispatcher
    def send_message(self, to: str, message_type: MessageType, payload: Dict[str, Any],
                     correlation_id: Optional[str] = None) -> MCPMessage:
        return self.send(to_agent=to, msg_type=message_type, payload=payload,
                         correlation_id=correlation_id)

    def receive(self) -> List[MCPMessage]:
        return self.transport.receive(self.agent_name)

    def process_inbox(self) -> List[MCPMessage]:
        """Process all pending messages and return responses generated."""
        responses = []
        for msg in self.receive():
            handler = self._handlers.get(msg.message_type)
            if handler:
                try:
                    response = handler(msg)
                    if response:
                        responses.append(response)
                except Exception as e:
                    logger.exception(f"Handler error for {msg.message_type}: {e}")
                    err = self.send(
                        to_agent=msg.from_agent,
                        msg_type=MessageType.ERROR,
                        payload={"error": str(e), "original_message_id": msg.message_id},
                        correlation_id=msg.correlation_id
                    )
                    responses.append(err)
            else:
                logger.warning(f"No handler registered for {msg.message_type}")
        return responses

    # --- Convenience Methods for Common Patterns ---

    def delegate_task(self, to_agent: str, task_description: str, context: Dict[str, Any],
                      priority: int = 3) -> MCPMessage:
        """High-level helper to delegate work to a sub-agent."""
        return self.send(
            to_agent=to_agent,
            msg_type=MessageType.TASK_REQUEST,
            payload={
                "task": task_description,
                "context": context,
                "requested_by": self.agent_name
            },
            priority=priority,
            tags=["delegation"]
        )

    def report_result(self, to_agent: str, correlation_id: str, result: Any, success: bool = True):
        return self.send(
            to_agent=to_agent,
            msg_type=MessageType.TASK_RESULT,
            payload={"result": result, "success": success},
            correlation_id=correlation_id
        )

    def share_memory(self, to_agent: str, key: str, value: Any, namespace: str = "global"):
        return self.send(
            to_agent=to_agent,
            msg_type=MessageType.MEMORY_UPDATE,
            payload={"key": key, "value": value, "namespace": namespace}
        )

    def propose_self_improvement(self, proposal: str, rationale: str, expected_impact: str):
        return self.send(
            to_agent="hermes",  # or a dedicated meta-agent
            msg_type=MessageType.SELF_IMPROVEMENT_PROPOSAL,
            payload={
                "proposal": proposal,
                "rationale": rationale,
                "expected_impact": expected_impact
            },
            priority=2,
            tags=["self-improvement"]
        )

    # --- Default Handlers ---

    def _handle_heartbeat(self, msg: MCPMessage) -> Optional[MCPMessage]:
        logger.info(f"Heartbeat from {msg.from_agent}")
        return None

    def _handle_error(self, msg: MCPMessage) -> Optional[MCPMessage]:
        logger.error(f"Error from {msg.from_agent}: {msg.payload}")
        return None


# =============================================================================
# Agent Registry (Simple file-backed for now)
# =============================================================================

class AgentRegistry:
    """Lightweight registry so agents can discover each other."""

    def __init__(self, path: Path = Path("mcp/registry.json")):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict:
        return json.loads(self.path.read_text())

    def _write(self, data: Dict):
        self.path.write_text(json.dumps(data, indent=2))

    def register(self, name: str, capabilities: List[str], metadata: Optional[Dict] = None):
        data = self._read()
        data[name] = {
            "capabilities": capabilities,
            "last_seen": time.time(),
            "metadata": metadata or {}
        }
        self._write(data)

    def deregister(self, name: str):
        data = self._read()
        data.pop(name, None)
        self._write(data)

    def list_agents(self) -> Dict:
        return self._read()

    def find_agents_with_capability(self, capability: str) -> List[str]:
        return [name for name, info in self._read().items() 
                if capability in info.get("capabilities", [])]


# =============================================================================
# Example: Base Sub-Agent Class
# =============================================================================

class BaseMCPAgent:
    """Base class for any Hermes sub-agent that speaks MCP."""

    def __init__(self, name: str, mcp: Optional[MCPProtocol] = None):
        self.name = name
        self.mcp = mcp or MCPProtocol(agent_name=name)
        self.registry = AgentRegistry()
        self.registry.register(name, capabilities=self.get_capabilities())

    def get_capabilities(self) -> List[str]:
        return ["general"]

    def run_loop(self, poll_interval: float = 2.0):
        """Simple blocking loop for agents that run continuously."""
        logger.info(f"Starting MCP agent loop: {self.name}")
        try:
            while True:
                responses = self.mcp.process_inbox()
                for r in responses:
                    if r.to_agent != "broadcast":
                        self.mcp.transport.send(r)
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info(f"Agent {self.name} shutting down...")
            self.registry.deregister(self.name)


if __name__ == "__main__":
    # Quick self-test
    print("MCP Protocol module loaded successfully.")
    print("Available message types:", [t.value for t in MessageType])