"""
Long-Horizon Planner Agent
==========================

Breaks down long-term goals into daily/weekly tasks and tracks progress.
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("LongHorizonPlannerAgent")


class LongHorizonPlannerAgent(BaseMCPAgent):
    def __init__(self, name: str = "long_horizon_planner"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "goal_decomposition",
            "task_scheduling",
            "progress_tracking",
            "plan_adjustment"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        goal = context.get("goal", "")

        logger.info(f"LongHorizonPlanner received goal: {goal}")

        result = {
            "status": "completed",
            "goal": goal,
            "decomposed_tasks": [
                {"task": "Research current state", "deadline": "Day 1"},
                {"task": "Design solution", "deadline": "Day 3"},
                {"task": "Implement core", "deadline": "Day 7"}
            ],
            "estimated_duration_days": 14
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
    run_agent(LongHorizonPlannerAgent())