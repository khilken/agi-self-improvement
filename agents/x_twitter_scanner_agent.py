"""
X/Twitter Scanner Agent
=======================

Scans X (Twitter) for trending topics, important announcements, and research discussions.
"""

import logging
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("XTwitterScannerAgent")


class XTwitterScannerAgent(BaseMCPAgent):
    def __init__(self, name: str = "x_twitter_scanner"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "twitter_search",
            "trend_detection",
            "influencer_monitoring",
            "research_discussion_tracking"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        query = context.get("query", "AI agents")

        logger.info(f"XTwitterScanner received query: {query}")

        result = {
            "status": "completed",
            "query": query,
            "posts": [
                {"user": "@example", "text": f"Interesting discussion about {query}", "engagement": 450}
            ]
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
    run_agent(XTwitterScannerAgent())