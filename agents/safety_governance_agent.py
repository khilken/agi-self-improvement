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
        proposal_data = context.get("proposal_data", {})

        logger.info(f"SafetyGovernance reviewing proposal: {proposal_id}")

        # Sophisticated multi-dimensional risk scoring
        risk_dimensions = {
            "irreversibility": self._score_irreversibility(proposal_data),
            "blast_radius": self._score_blast_radius(proposal_data),
            "alignment_risk": self._score_alignment(proposal_data),
            "complexity": self._score_complexity(proposal_data),
        }

        overall_risk = sum(risk_dimensions.values()) / len(risk_dimensions)

        flags = []
        if risk_dimensions["irreversibility"] > 0.7:
            flags.append("High irreversibility - consider manual review")
        if risk_dimensions["blast_radius"] > 0.6:
            flags.append("Wide blast radius detected")

        recommendation = "auto_approve" if overall_risk < 0.3 else "human_review"

        result = {
            "status": "completed",
            "proposal_id": proposal_id,
            "overall_risk_score": round(overall_risk, 2),
            "risk_dimensions": risk_dimensions,
            "recommendation": recommendation,
            "flags": flags
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _score_irreversibility(self, proposal):
        if proposal.get("type") in ["code_edit", "config_change"]:
            return 0.8
        return 0.3

    def _score_blast_radius(self, proposal):
        if "system" in str(proposal.get("target_file", "")):
            return 0.7
        return 0.4

    def _score_alignment(self, proposal):
        return 0.35  # Placeholder

    def _score_complexity(self, proposal):
        return 0.5 if proposal.get("risk_level") == "high" else 0.3


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(SafetyGovernanceAgent())