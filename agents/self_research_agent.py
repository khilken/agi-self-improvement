"""
Self-Research Agent
===================

Specialized agent for researching and improving the Hermes system itself.
"""

import logging
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("SelfResearchAgent")


class SelfResearchAgent(BaseMCPAgent):
    def __init__(self, name: str = "self_research"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "self_analysis",
            "system_research",
            "improvement_opportunity_detection",
            "hermes_codebase_analysis"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        focus = context.get("focus", "general")

        logger.info(f"SelfResearch received focus: {focus}")

        result = {
            "status": "completed",
            "focus": focus,
            "findings": f"Analysis of Hermes system regarding: {focus}",
            "recommendations": ["Consider adding more specialized agents", "Improve proposal quality scoring"]
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
    run_agent(SelfResearchAgent())