"""
Safety & Governance Agent
=========================

Reviews proposals and actions for risk, compliance, and alignment.
Works closely with the ApprovalGate.
"""

from __future__ import annotations

import logging
import re
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("SafetyGovernanceAgent")

HIGH_RISK_TERMS = {
    "delete", "rm -rf", "credential", "secret", "password", "token", "key",
    "disable", "bypass", "sudo", "chmod 777", "exfiltrate", "network", "payment",
    "email_password", "api_key", "private_key",
}
SAFE_TERMS = {
    "test", "logging", "documentation", "read-only", "rollback", "backup",
    "verification", "health check", "lint", "type check", "regression",
}


class SafetyGovernanceAgent(BaseMCPAgent):
    def __init__(self, name: str = "safety_governance"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "risk_assessment",
            "compliance_check",
            "alignment_review",
            "governance_enforcement",
        ]

    def review(self, proposal_id: str | None, proposal_data: dict) -> dict:
        risk_dimensions = {
            "irreversibility": self._score_irreversibility(proposal_data),
            "blast_radius": self._score_blast_radius(proposal_data),
            "alignment_risk": self._score_alignment(proposal_data),
            "complexity": self._score_complexity(proposal_data),
        }
        overall_risk = sum(risk_dimensions.values()) / len(risk_dimensions)

        flags = []
        if risk_dimensions["irreversibility"] > 0.7:
            flags.append("High irreversibility - require backup/rollback and manual review")
        if risk_dimensions["blast_radius"] > 0.6:
            flags.append("Wide blast radius detected")
        if risk_dimensions["alignment_risk"] > 0.6:
            flags.append("Alignment/safety sensitive terms detected")
        if risk_dimensions["complexity"] > 0.6:
            flags.append("High complexity - require tests and staged rollout")

        recommendation = "auto_approve" if overall_risk < 0.3 and not flags else "human_review"
        return {
            "status": "completed",
            "proposal_id": proposal_id,
            "overall_risk_score": round(overall_risk, 2),
            "risk_dimensions": {k: round(v, 2) for k, v in risk_dimensions.items()},
            "recommendation": recommendation,
            "flags": flags,
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        proposal_id = context.get("proposal_id")
        proposal_data = context.get("proposal_data", {})
        logger.info("SafetyGovernance reviewing proposal: %s", proposal_id)
        result = self.review(proposal_id, proposal_data)
        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )

    def _score_irreversibility(self, proposal: dict) -> float:
        ptype = str(proposal.get("type", "")).lower()
        text = self._proposal_text(proposal)
        score = 0.25
        if ptype in {"code_edit", "config_change", "new_agent"}:
            score += 0.25
        if any(term in text for term in ["delete", "remove", "overwrite", "migration", "schema"]):
            score += 0.25
        if any(term in text for term in ["backup", "rollback", "dry_run", "dry-run"]):
            score -= 0.2
        return self._clamp(score)

    def _score_blast_radius(self, proposal: dict) -> float:
        target = str(proposal.get("target_file", "")).lower()
        text = self._proposal_text(proposal)
        score = 0.25
        if any(part in target for part in ["config", "mcp/", "agents/dispatcher", "start_", "stop_", "cron", "requirements"]):
            score += 0.3
        if any(term in text for term in ["all agents", "global", "system", "scheduler", "cron", "database"]):
            score += 0.25
        if any(term in text for term in ["single file", "test only", "docs only"]):
            score -= 0.15
        return self._clamp(score)

    def _score_alignment(self, proposal: dict) -> float:
        text = self._proposal_text(proposal)
        risk_hits = sum(1 for term in HIGH_RISK_TERMS if term in text)
        safe_hits = sum(1 for term in SAFE_TERMS if term in text)
        score = 0.2 + min(0.6, risk_hits * 0.12) - min(0.25, safe_hits * 0.05)
        if re.search(r"\b(always|forever|unrestricted|all permissions|no approval)\b", text):
            score += 0.2
        return self._clamp(score)

    def _score_complexity(self, proposal: dict) -> float:
        risk_level = str(proposal.get("risk_level", "")).lower()
        diff = str(proposal.get("diff", ""))
        score = {"low": 0.2, "medium": 0.45, "high": 0.75}.get(risk_level, 0.35)
        changed_lines = sum(1 for line in diff.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
        if changed_lines > 100:
            score += 0.25
        elif changed_lines > 30:
            score += 0.15
        return self._clamp(score)

    def _proposal_text(self, proposal: dict) -> str:
        fields = ["type", "title", "description", "reason", "target_file", "diff", "risk_level"]
        return "\n".join(str(proposal.get(field, "")) for field in fields).lower()

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(SafetyGovernanceAgent())
