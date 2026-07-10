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

        # Get all proposals
        all_proposals = self.proposal_store.list_all()

        for proposal in all_proposals:
            if proposal.risk_level != RiskLevel.LOW:
                continue

            # Check if already processed
            approval = self.approval_gate.get_status(proposal.id)
            if approval and approval.status != "pending":
                continue

            # Self-verification before auto-apply
            if not self._verify_proposal(proposal):
                logger.warning(f"Proposal {proposal.id} failed verification - skipping")
                continue

            # Auto-apply
            try:
                self._apply_proposal(proposal)
                applied.append(proposal.id)
                logger.info(f"Auto-applied low-risk proposal: {proposal.title}")
            except Exception as e:
                logger.error(f"Failed to auto-apply {proposal.id}: {e}")

        return applied

    def _apply_proposal(self, proposal):
        """Apply a proposal (placeholder for real implementation)."""
        # In a real system, this would:
        # - Apply code diffs
        # - Update prompt files
        # - Register new skills
        # etc.

        # For now, just record the application
        self.history.record(HistoryEvent(
            event_type=HistoryEventType.APPLIED,
            proposal_id=proposal.id,
            actor="auto_apply_engine",
            details={"type": proposal.type.value, "title": proposal.title}
        ))

        # Mark as approved (auto)
        self.approval_gate.approve(
            proposal.id,
            reviewer="auto_apply_engine",
            notes="Automatically approved (low risk)"
        )