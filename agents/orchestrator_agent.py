"""
Orchestrator Agent for Hermes
=============================

Coordinates multi-step workflows with reflection:
Task → Target Agent → Evaluator → (optional) Meta-Improver
"""

import logging
from typing import List, Dict, Any

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from agents.dispatcher import HermesDispatcher

logger = logging.getLogger("OrchestratorAgent")


class OrchestratorAgent(BaseMCPAgent):
    def __init__(self, name: str = "orchestrator"):
        super().__init__(name=name)
        self.dispatcher = HermesDispatcher()
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "workflow_orchestration",
            "reflection_loop",
            "multi_agent_coordination"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        workflow = context.get("workflow", "reflective_task")
        target = context.get("target_agent", "researcher")
        task_type = context.get("task_type", "research")
        task_context = context.get("task_context", {})

        logger.info(f"Orchestrator received workflow: {workflow}")

        if workflow == "reflective_task":
            result = self.dispatcher.run_with_reflection(target, task_type, task_context)
        else:
            result = {"status": "unknown_workflow"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = OrchestratorAgent()
    from agents.base_runner import run_agent
    run_agent(agent)
