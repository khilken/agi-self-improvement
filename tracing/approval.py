"""
Approval Gate System for Hermes
===============================

Implements Human-in-the-Loop (HITL) patterns for self-improving agents.
Based on 2026 best practices for safe agentic systems.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from pathlib import Path


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


@dataclass
class ApprovalRecord:
    proposal_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer: Optional[str] = None
    decision_time: Optional[str] = None
    notes: Optional[str] = None
    modified_diff: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "status": self.status.value,
            "reviewer": self.reviewer,
            "decision_time": self.decision_time,
            "notes": self.notes,
            "modified_diff": self.modified_diff,
        }


class ApprovalGate:
    """
    Approval Gate for improvement proposals.
    High-risk proposals require human approval before application.
    """

    def __init__(self, storage_dir: str = "logs/approvals"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def submit_for_approval(self, proposal_id: str) -> ApprovalRecord:
        """Submit a proposal for human review."""
        record = ApprovalRecord(proposal_id=proposal_id)
        self._save(record)
        return record

    def approve(self, proposal_id: str, reviewer: str, notes: str = "") -> ApprovalRecord:
        """Approve a proposal."""
        record = self._load(proposal_id) or ApprovalRecord(proposal_id=proposal_id)
        record.status = ApprovalStatus.APPROVED
        record.reviewer = reviewer
        record.decision_time = datetime.now().isoformat()
        record.notes = notes
        self._save(record)
        return record

    def reject(self, proposal_id: str, reviewer: str, notes: str = "") -> ApprovalRecord:
        """Reject a proposal."""
        record = self._load(proposal_id) or ApprovalRecord(proposal_id=proposal_id)
        record.status = ApprovalStatus.REJECTED
        record.reviewer = reviewer
        record.decision_time = datetime.now().isoformat()
        record.notes = notes
        self._save(record)
        return record

    def modify(self, proposal_id: str, reviewer: str, modified_diff: str, notes: str = "") -> ApprovalRecord:
        """Approve with modifications."""
        record = self._load(proposal_id) or ApprovalRecord(proposal_id=proposal_id)
        record.status = ApprovalStatus.MODIFIED
        record.reviewer = reviewer
        record.decision_time = datetime.now().isoformat()
        record.modified_diff = modified_diff
        record.notes = notes
        self._save(record)
        return record

    def get_status(self, proposal_id: str) -> Optional[ApprovalRecord]:
        return self._load(proposal_id)

    def list_pending(self) -> List[ApprovalRecord]:
        """List all proposals waiting for review."""
        pending = []
        for f in self.storage_dir.glob("approval_*.json"):
            with open(f, "r") as file:
                data = json.load(file)
                record = ApprovalRecord(**data)
                if record.status == ApprovalStatus.PENDING:
                    pending.append(record)
        return pending

    def _save(self, record: ApprovalRecord):
        filepath = self.storage_dir / f"approval_{record.proposal_id}.json"
        with open(filepath, "w") as f:
            json.dump(record.to_dict(), f, indent=2)

    def _load(self, proposal_id: str) -> Optional[ApprovalRecord]:
        filepath = self.storage_dir / f"approval_{proposal_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r") as f:
            data = json.load(f)
        return ApprovalRecord(**data)