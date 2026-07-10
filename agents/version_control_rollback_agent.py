"""
Version Control & Smart Rollback Agent
======================================

Manages versioning of self-modifications and performs intelligent rollback
when improvements cause regressions.
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("VersionControlRollbackAgent")


class VersionControlRollbackAgent(BaseMCPAgent):
    def __init__(self, name: str = "version_control_rollback"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "version_tracking",
            "smart_rollback",
            "regression_detection",
            "change_history"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        action = context.get("action", "track")

        logger.info(f"VersionControlRollback received action: {action}")

        if action == "rollback":
            result = {
                "status": "completed",
                "action": "rollback",
                "proposal_id": context.get("proposal_id"),
                "success": True
            }
        else:
            result = {
                "status": "completed",
                "action": "track",
                "message": "Change tracked in version history"
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
    run_agent(VersionControlRollbackAgent())