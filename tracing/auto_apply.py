"""
Low-Risk Auto-Apply System
==========================

Automatically applies low-risk improvement proposals without human review.
High and medium risk proposals still go through the ApprovalGate.
"""

from pathlib import Path
import json
import logging
from typing import List

from tracing.proposal import ProposalStore, ProposalType, RiskLevel
from tracing.approval import ApprovalGate
from tracing.history import ImprovementHistory, HistoryEvent, HistoryEventType

logger = logging.getLogger("AutoApply")


class AutoApplyEngine:
    """
    Automatically applies safe (low-risk) improvement proposals.
    """

    def __init__(self):
        self.proposal_store = ProposalStore()
        self.approval_gate = ApprovalGate()
        self.history = ImprovementHistory()

    def process_low_risk_proposals(self) -> List[str]:
        """
        Find all low-risk proposals that haven't been processed yet
        and apply them automatically.
        """
        applied = []

        all_proposals = self.proposal_store.list_all()

        for proposal in all_proposals:
            if proposal.risk_level != RiskLevel.LOW:
                continue

            approval = self.approval_gate.get_status(proposal.id)
            if approval and str(getattr(approval, "status", approval)) not in (
                "pending",
                "ApprovalStatus.PENDING",
                "PENDING",
            ):
                # Already handled
                status_val = getattr(approval, "status", approval)
                if str(status_val).lower() not in ("pending", "approvalstatus.pending"):
                    continue

            if not self._verify_proposal(proposal):
                logger.warning(f"Proposal {proposal.id} failed verification - skipping")
                continue

            try:
                self._apply_proposal(proposal)
                applied.append(proposal.id)
                logger.info(f"Auto-applied low-risk proposal: {proposal.title}")
            except Exception as e:
                logger.error(f"Failed to auto-apply {proposal.id}: {e}")

        return applied

    def _verify_proposal(self, proposal) -> bool:
        """Lightweight safety checks before auto-applying a low-risk proposal."""
        if not proposal or not getattr(proposal, "id", None):
            return False
        if not getattr(proposal, "title", None):
            return False
        if proposal.risk_level != RiskLevel.LOW:
            return False
        if not getattr(proposal, "reason", None):
            logger.warning(f"Proposal {proposal.id} missing reason")
            return False
        return True

    def _apply_proposal(self, proposal):
        """Apply a proposal (record + mark approved for low-risk)."""
        self.history.record(HistoryEvent(
            event_type=HistoryEventType.APPLIED,
            proposal_id=proposal.id,
            actor="auto_apply_engine",
            details={"type": proposal.type.value, "title": proposal.title},
        ))

        self.approval_gate.approve(
            proposal.id,
            reviewer="auto_apply_engine",
            notes="Automatically approved (low risk)",
        )
