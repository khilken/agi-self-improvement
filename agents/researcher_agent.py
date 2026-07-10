"""
Researcher Sub-Agent for Hermes
==============================

Specialized MCP-enabled agent for web research, paper reading, 
information synthesis, and knowledge acquisition.
"""

import logging
import ollama
import json
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

try:
    from tasks.task_queue import claim_task, complete_task, fail_task
    TASK_QUEUE_AVAILABLE = True
except ImportError:
    TASK_QUEUE_AVAILABLE = False
    claim_task = complete_task = fail_task = lambda *a, **k: None

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

    def _call_llm(self, prompt: str, model: str = "qwen2.5:32b"):
        try:
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def handle_task_request(self, msg: MCPMessage):
        print(f"[DEBUG] {self.__class__.__name__} received: {msg.message_type} from {msg.from_agent}")
        task_type = msg.payload.get("task_type", "research")
        context = msg.payload.get("context", {})
        query = context.get("query", "")

        logger.info(f"Researcher received task: {task_type} | query={query}")

        # Placeholder for real implementation
        result = {
            "status": "completed",
            "task_type": task_type,
            "query": query,
            "summary": f"Research completed for: {query}",
            "sources": []
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

        if TASK_QUEUE_AVAILABLE:
            complete_task(msg.payload.get("task_id"))
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = ResearcherAgent()
    from agents.base_runner import run_agent
    run_agent(agent)
