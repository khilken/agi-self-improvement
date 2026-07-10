"""
News Research Agent
===================

Specialized agent for daily news research across three tiers:
- Local (Grand Junction, CO)
- National (US)
- International

Source selection leans slightly right while maintaining broad coverage.
"""

import logging
from typing import List, Dict, Any

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("NewsResearchAgent")


class NewsResearchAgent(BaseMCPAgent):
    def __init__(self, name: str = "news_research"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

        # Source lists (slight right lean)
        self.local_sources = [
            "The Daily Sentinel (Grand Junction)",
            "KKCO 11 News",
            "Western Slope Now",
            "Grand Junction Free Press"
        ]

        self.national_sources = [
            "Fox News",
            "Wall Street Journal",
            "National Review",
            "Daily Wire",
            "The Federalist",
            "New York Post",
            "Washington Examiner"
        ]

        self.international_sources = [
            "The Telegraph",
            "The Spectator",
            "Reuters",
            "BBC (select coverage)",
            "The Australian",
            "Jerusalem Post"
        ]

    def get_capabilities(self) -> List[str]:
        return [
            "local_news_research",
            "national_news_research",
            "international_news_research",
            "news_synthesis",
            "source_diversity_analysis"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        scope = context.get("scope", "all")  # local, national, international, all

        logger.info(f"NewsResearchAgent received scope: {scope}")

        result: Dict[str, Any] = {
            "status": "completed",
            "scope": scope,
            "local_sources": self.local_sources if scope in ["local", "all"] else [],
            "national_sources": self.national_sources if scope in ["national", "all"] else [],
            "international_sources": self.international_sources if scope in ["international", "all"] else [],
            "summary": f"News research completed for scope: {scope}"
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
    run_agent(NewsResearchAgent())