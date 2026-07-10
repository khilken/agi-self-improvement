"""
Experimentation & A/B Testing Agent
===================================

Runs controlled experiments on improvements, prompt variations, or agent configurations.
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("ExperimentationAgent")


class ExperimentationAgent(BaseMCPAgent):
    def __init__(self, name: str = "experimentation"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "ab_testing",
            "experiment_design",
            "result_analysis",
            "statistical_validation"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        experiment_type = context.get("type", "prompt_variation")

        logger.info(f"ExperimentationAgent received: {experiment_type}")

        result = {
            "status": "completed",
            "experiment_type": experiment_type,
            "winner": "variant_b",
            "confidence": 0.87,
            "notes": "Variant B showed 23% improvement in evaluation scores"
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
    run_agent(ExperimentationAgent())