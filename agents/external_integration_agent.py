"""
External Integration Agent
==========================

Handles connections to external platforms (Slack, Telegram, Notion, Email, etc.).
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("ExternalIntegrationAgent")


class ExternalIntegrationAgent(BaseMCPAgent):
    def __init__(self, name: str = "external_integration"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "slack_messaging",
            "telegram_messaging",
            "notion_update",
            "email_sending",
            "webhook_trigger"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        platform = context.get("platform", "email")
        content = context.get("content", "")

        logger.info(f"ExternalIntegration sending to {platform}")

        result = {
            "status": "completed",
            "platform": platform,
            "message": f"Sent to {platform}: {content[:50]}..."
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
    run_agent(ExternalIntegrationAgent())