"""
Proposal Application & Rollback Engine
======================================

Applies approved improvement proposals and supports rollback.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from tracing.proposal import ImprovementProposal, ProposalType
from tracing.history import ImprovementHistory, HistoryEvent, HistoryEventType


class ProposalApplicator:
    """
    Applies and rolls back improvement proposals.
    """

    def __init__(self, backup_dir: str = "logs/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.history = ImprovementHistory()

    def apply(self, proposal: ImprovementProposal) -> bool:
        """Apply a proposal."""
        if not proposal.target_file or not proposal.diff:
            # For non-code proposals, just record the event
            self.history.record(HistoryEvent(
                event_type=HistoryEventType.APPLIED,
                proposal_id=proposal.id,
                details={"note": "Non-code proposal applied"}
            ))
            return True

        target = Path(proposal.target_file)
        if not target.exists():
            return False

        # Create backup
        backup_path = self.backup_dir / f"{target.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        shutil.copy2(target, backup_path)

        # Apply diff (very basic for now)
        # In production this would use proper patch/diff tools
        try:
            # Placeholder: real implementation would apply the diff
            self.history.record(HistoryEvent(
                event_type=HistoryEventType.APPLIED,
                proposal_id=proposal.id,
                details={"backup": str(backup_path)}
            ))
            return True
        except Exception as e:
            # Rollback on failure
            shutil.copy2(backup_path, target)
            return False

    def rollback(self, proposal_id: str, backup_path: str) -> bool:
        """Rollback a change using a backup."""
        backup = Path(backup_path)
        if not backup.exists():
            return False

        # Find original file from backup name (simplified)
        original_name = backup.stem.split(".")[0]
        original = Path(original_name)

        if original.exists():
            shutil.copy2(backup, original)

        self.history.record(HistoryEvent(
            event_type=HistoryEventType.ROLLED_BACK,
            proposal_id=proposal_id,
            details={"backup_used": str(backup)}
        ))
        return True