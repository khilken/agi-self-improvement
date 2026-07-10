"""
Web Search Agent
================

Specialized agent for web search, result synthesis, and source verification.
"""

import logging
import ollama
import json
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("WebSearchAgent")


class WebSearchAgent(BaseMCPAgent):
    def __init__(self, name: str = "web_search"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "web_search",
            "result_synthesis",
            "source_verification",
            "trend_detection"
        ]

    def _call_llm(self, prompt: str, model: str = "qwen2.5:32b"):
        try:
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        query = context.get("query", "")

        logger.info(f"WebSearch received query: {query}")

        # Placeholder for real web search implementation
        result = {
            "status": "completed",
            "query": query,
            "results": [
                {"title": f"Result for {query}", "url": "https://example.com", "snippet": "Example snippet..."}
            ],
            "synthesis": f"Synthesized summary for: {query}"
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(WebSearchAgent())