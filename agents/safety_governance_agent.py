"""
Safety & Governance Agent
=========================

Reviews proposals and actions for risk, compliance, and alignment.
Works closely with the ApprovalGate.
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("SafetyGovernanceAgent")


class SafetyGovernanceAgent(BaseMCPAgent):
    def __init__(self, name: str = "safety_governance"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "risk_assessment",
            "compliance_check",
            "alignment_review",
            "governance_enforcement"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        proposal_id = context.get("proposal_id")

        logger.info(f"SafetyGovernance reviewing proposal: {proposal_id}")

        # Placeholder risk scoring
        result = {
            "status": "completed",
            "proposal_id": proposal_id,
            "risk_score": 0.45,
            "recommendation": "proceed_with_review",
            "flags": []
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
    run_agent(SafetyGovernanceAgent())