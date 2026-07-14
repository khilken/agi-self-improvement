"""
Long-Horizon Planner Agent
==========================

Breaks down long-term goals into daily/weekly tasks and tracks progress.
"""

import logging
from typing import Any, List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from agents.dispatcher import HermesDispatcher

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

        # Decompose goal and dispatch tasks to other agents
        d = HermesDispatcher()
        tasks: list[dict[str, Any]] = [
            {"agent": "researcher", "task_type": "research", "context": {"query": f"Research for: {goal}"}},
            {"agent": "knowledge_curator", "task_type": "organize", "context": {"topic": goal}},
            {"agent": "safety_governance", "task_type": "review", "context": {"topic": goal}}
        ]

        for task in tasks:
            d.dispatch(task["agent"], task["task_type"], task["context"])

        result = {
            "status": "completed",
            "goal": goal,
            "tasks_dispatched": len(tasks),
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