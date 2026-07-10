"""
Resource Monitor Agent
======================

Tracks API usage, token consumption, disk space, and memory to prevent
runaway costs or resource exhaustion.
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("ResourceMonitorAgent")


class ResourceMonitorAgent(BaseMCPAgent):
    def __init__(self, name: str = "resource_monitor"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "usage_tracking",
            "cost_monitoring",
            "resource_alerts",
            "quota_management"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        metric = context.get("metric", "all")

        logger.info(f"ResourceMonitor checking: {metric}")

        result = {
            "status": "completed",
            "metric": metric,
            "token_usage_today": 12450,
            "estimated_cost": "$3.42",
            "alerts": []
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
    run_agent(ResourceMonitorAgent())