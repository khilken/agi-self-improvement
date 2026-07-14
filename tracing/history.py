"""
Improvement History System
==========================

Tracks the full history of improvement proposals, approvals, and applications.
Enables versioning, rollback, and audit trails.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import json
from pathlib import Path


class HistoryEventType(str, Enum):
    PROPOSAL_CREATED = "proposal_created"
    APPROVAL_SUBMITTED = "approval_submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"


@dataclass
class HistoryEvent:
    event_type: HistoryEventType
    proposal_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    actor: str = "system"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "details": self.details,
        }


class ImprovementHistory:
    """Manages the complete history of the self-improvement process."""

    def __init__(self, storage_dir: str = "logs/history"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.storage_dir / "history.jsonl"

    def record(self, event: HistoryEvent):
        """Append an event to the history log."""
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def get_history(self, proposal_id: Optional[str] = None) -> List[HistoryEvent]:
        """Retrieve history, optionally filtered by proposal."""
        events: List[HistoryEvent] = []
        if not self.events_file.exists():
            return events

        with open(self.events_file, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    event = HistoryEvent(
                        event_type=HistoryEventType(data["event_type"]),
                        proposal_id=data["proposal_id"],
                        timestamp=data["timestamp"],
                        actor=data.get("actor", "system"),
                        details=data.get("details", {})
                    )
                    if proposal_id is None or event.proposal_id == proposal_id:
                        events.append(event)
        return events

    def get_timeline(self, limit: int = 50) -> List[HistoryEvent]:
        """Get the most recent events."""
        events = self.get_history()
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]