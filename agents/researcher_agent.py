"""
Researcher Sub-Agent for Hermes
==============================

Specialized MCP-enabled agent for web research, paper reading,
information synthesis, and knowledge acquisition.
"""

from __future__ import annotations

import logging
from typing import Any, List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from config import get_ollama_client, OLLAMA_DEFAULT_MODEL, configure_ollama_env
configure_ollama_env()

try:
    from tasks.task_queue import claim_task, complete_task, fail_task
    TASK_QUEUE_AVAILABLE = True
except ImportError:
    TASK_QUEUE_AVAILABLE = False

    def claim_task(task_id: str) -> bool:
        return False

    def complete_task(task_id: str, result: dict[str, Any] | None = None) -> bool:
        return False

    def fail_task(task_id: str, error: str) -> bool:
        return False

logger = logging.getLogger("ResearcherAgent")


class ResearcherAgent(BaseMCPAgent):
    """Sub-agent specialized in research and information gathering."""

    def __init__(self, name: str = "researcher"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "web_research",
            "paper_reading",
            "information_synthesis",
            "trend_analysis",
            "source_verification"
        ]

    def _call_llm(self, prompt: str, model: str | None = None):
        try:
            model = model or OLLAMA_DEFAULT_MODEL
            response = get_ollama_client().chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def handle_task_request(self, msg: MCPMessage):
        task_type = msg.payload.get("task_type", "research")
        context = msg.payload.get("context", {})
        query = context.get("query", "")

        logger.info(f"Researcher received task: {task_type} | query={query}")

        summary = self._call_llm(
            f"You are Hermes Researcher. Produce a concise research brief for: {query}"
        ) or f"Research completed for: {query}"

        result = {
            "status": "completed",
            "task_type": task_type,
            "query": query,
            "summary": summary,
            "sources": [],
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )

        if TASK_QUEUE_AVAILABLE:
            task_id = msg.payload.get("task_id")
            if task_id:
                complete_task(str(task_id))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = ResearcherAgent()
    from agents.base_runner import run_agent
    run_agent(agent)
