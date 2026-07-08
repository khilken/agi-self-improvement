"""
Hermes Task Dispatcher
======================

Simple dispatcher that routes tasks to specialized sub-agents
using the MCP protocol.

Usage:
    from agents.dispatcher import dispatch_task

    dispatch_task("researcher", "research", {"query": "Latest AGI papers"})
    dispatch_task("coder", "code", {"description": "Create a FastAPI endpoint"})
"""

import logging
from typing import Any, Dict, Optional

from mcp.protocol import MCPProtocol, MessageType

logger = logging.getLogger("Dispatcher")


class HermesDispatcher:
    def __init__(self, agent_name: str = "hermes_dispatcher"):
        self.mcp = MCPProtocol(agent_name=agent_name)
        self.agents = {
            "researcher": "researcher",
            "coder": "coder",
            "memory_synthesizer": "memory_synthesizer",
        }

    def dispatch(
        self,
        target_agent: str,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        """Send a task to a specific sub-agent."""
        if target_agent not in self.agents:
            logger.warning(f"Unknown agent: {target_agent}")
            return None

        payload = {
            "task_type": task_type,
            "context": context or {},
        }

        logger.info(f"Dispatching {task_type} to {target_agent}")

        self.mcp.send_message(
            to=target_agent,
            message_type=MessageType.TASK_REQUEST,
            payload=payload,
            correlation_id=correlation_id,
        )
        return correlation_id

    def dispatch_research(self, query: str):
        return self.dispatch("researcher", "research", {"query": query})

    def dispatch_coding(self, description: str):
        return self.dispatch("coder", "code", {"description": description})

    def dispatch_memory_synthesis(self, task_type: str = "full_synthesis"):
        return self.dispatch("memory_synthesizer", task_type, {})


# Convenience function
def dispatch_task(target: str, task_type: str, context: Optional[Dict] = None):
    dispatcher = HermesDispatcher()
    return dispatcher.dispatch(target, task_type, context)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    d = HermesDispatcher()

    # Example usage
    print("Dispatching example tasks...")
    d.dispatch_research("Latest developments in AGI self-improvement")
    d.dispatch_coding("Create a FastAPI health check endpoint with logging")
    d.dispatch_memory_synthesis("full_synthesis")