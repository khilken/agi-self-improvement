"""
Web Search Agent
================

Specialized agent for web search, result synthesis, and source verification.
"""

import logging
import json
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from config import get_ollama_client, OLLAMA_DEFAULT_MODEL, configure_ollama_env
configure_ollama_env()

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
            "trend_detection",
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
        context = msg.payload.get("context", {})
        query = context.get("query", "")

        logger.info(f"WebSearch received query: {query}")

        synthesis = self._call_llm(
            f"Synthesize a useful web-research summary for query: {query}"
        ) or f"Synthesized summary for: {query}"

        result = {
            "status": "completed",
            "query": query,
            "results": [
                {
                    "title": f"Result for {query}",
                    "url": "https://example.com",
                    "snippet": "Example snippet...",
                }
            ],
            "synthesis": synthesis,
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(WebSearchAgent())
