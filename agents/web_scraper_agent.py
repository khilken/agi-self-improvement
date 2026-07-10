"""
Web Scraper Agent
=================

Specialized agent for targeted web scraping and data extraction.
"""

import logging
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("WebScraperAgent")


class WebScraperAgent(BaseMCPAgent):
    def __init__(self, name: str = "web_scraper"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "web_scraping",
            "data_extraction",
            "structured_parsing",
            "content_monitoring"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        url = context.get("url", "")
        selector = context.get("selector", "")

        logger.info(f"WebScraper received: url={url}, selector={selector}")

        result = {
            "status": "completed",
            "url": url,
            "extracted_data": f"Extracted content from {url} using selector '{selector}'"
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
    run_agent(WebScraperAgent())