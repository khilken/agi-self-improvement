"""
Hermes MCP (Multi-Agent Communication Protocol) Package
=======================================================

This package provides a robust, persistent, file-backed communication protocol
for Hermes and its sub-agents.

Key Components:
- MCPMessage & MessageType: Standardized message envelope
- FileTransport: Persistent, auditable, git-friendly message queues
- MCPProtocol: High-level API for sending, receiving, delegating tasks
- AgentRegistry: Discovery of available agents and capabilities
- BaseMCPAgent: Foundation for building specialized sub-agents

Usage in Hermes main loop:
    from mcp.protocol import MCPProtocol, MessageType

    mcp = MCPProtocol(agent_name="hermes")
    mcp.delegate_task("researcher", "Find latest papers on self-improving agents", {...})
"""

from .protocol import (
    MCPMessage,
    MessageType,
    FileTransport,
    MCPProtocol,
    AgentRegistry,
    BaseMCPAgent,
)

__version__ = "0.1.0"
__all__ = [
    "MCPMessage",
    "MessageType",
    "FileTransport",
    "MCPProtocol",
    "AgentRegistry",
    "BaseMCPAgent",
]