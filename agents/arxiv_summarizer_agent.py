"""
arXiv Paper Summarizer Agent
============================

Specialized agent for fetching, summarizing, and extracting insights from arXiv papers.
"""

import logging
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("ArxivSummarizerAgent")


class ArxivSummarizerAgent(BaseMCPAgent):
    def __init__(self, name: str = "arxiv_summarizer"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "arxiv_search",
            "paper_summarization",
            "insight_extraction",
            "trend_analysis"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        query = context.get("query", "AI agents")

        logger.info(f"ArxivSummarizer received query: {query}")

        result = {
            "status": "completed",
            "query": query,
            "papers": [
                {
                    "title": f"Example Paper on {query}",
                    "summary": "This paper proposes a novel approach...",
                    "url": "https://arxiv.org/abs/xxxx.xxxxx"
                }
            ],
            "insights": f"Key trends in {query} research"
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
    run_agent(ArxivSummarizerAgent())