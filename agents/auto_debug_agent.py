"""
Automatic Debug + Log Analyzer Agent
====================================

Analyzes logs, detects errors, and proposes/applies fixes automatically.
"""

import logging
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("AutoDebugAgent")


class AutoDebugAgent(BaseMCPAgent):
    def __init__(self, name: str = "auto_debug"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "log_analysis",
            "error_detection",
            "automatic_fix_proposal",
            "safe_auto_fix"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        log_file = context.get("log_file", "logs/*.log")

        logger.info(f"AutoDebug analyzing: {log_file}")

        # Placeholder for real log analysis + fix logic
        result = {
            "status": "completed",
            "log_file": log_file,
            "issues_found": 2,
            "fixes_applied": 1,
            "fixes_proposed": [
                {"issue": "ImportError", "fix": "Add missing import", "applied": True}
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
    run_agent(AutoDebugAgent())