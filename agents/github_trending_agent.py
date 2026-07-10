"""
GitHub Trending Monitor Agent
=============================

Monitors trending repositories, new tools, and interesting projects on GitHub.
"""

import logging
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("GithubTrendingAgent")


class GithubTrendingAgent(BaseMCPAgent):
    def __init__(self, name: str = "github_trending"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "github_trending",
            "repository_analysis",
            "tool_discovery",
            "star_watch"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        topic = context.get("topic", "ai-agents")

        logger.info(f"GithubTrending received topic: {topic}")

        result = {
            "status": "completed",
            "topic": topic,
            "trending_repos": [
                {"name": f"example/{topic}-repo", "stars": 1234, "description": "Trending repo"}
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
    run_agent(GithubTrendingAgent())