"""
Structured Improvement Proposal Model
=====================================

Based on 2026 best practices (Hyperagents / Darwin Gödel Machine patterns).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json
from pathlib import Path


class ProposalType(str, Enum):
    PROMPT_CHANGE = "prompt_change"
    CODE_EDIT = "code_edit"
    NEW_SKILL = "new_skill"
    NEW_AGENT = "new_agent"
    CONFIG_CHANGE = "config_change"
    PROCESS_IMPROVEMENT = "process_improvement"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ImprovementProposal:
    id: str
    type: ProposalType
    title: str
    description: str
    reason: str
    target_file: Optional[str] = None
    diff: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    estimated_impact: str = ""
    priority: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "reason": self.reason,
            "target_file": self.target_file,
            "diff": self.diff,
            "risk_level": self.risk_level.value,
            "estimated_impact": self.estimated_impact,
            "priority": self.priority,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImprovementProposal":
        return cls(
            id=data["id"],
            type=ProposalType(data["type"]),
            title=data["title"],
            description=data["description"],
            reason=data["reason"],
            target_file=data.get("target_file"),
            diff=data.get("diff"),
            risk_level=RiskLevel(data["risk_level"]),
            estimated_impact=data.get("estimated_impact", ""),
            priority=data.get("priority", "medium"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


class ProposalStore:
    """Manages persistence of improvement proposals."""

    def __init__(self, storage_dir: str = "logs/improvements"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, proposal: ImprovementProposal) -> Path:
        filename = f"proposal_{proposal.id}.json"
        filepath = self.storage_dir / filename
        with open(filepath, "w") as f:
            f.write(proposal.to_json())
        return filepath

    def load(self, proposal_id: str) -> Optional[ImprovementProposal]:
        filepath = self.storage_dir / f"proposal_{proposal_id}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r") as f:
            data = json.load(f)
        return ImprovementProposal.from_dict(data)

    def list_all(self) -> list[ImprovementProposal]:
        proposals = []
        for f in sorted(self.storage_dir.glob("proposal_*.json"), reverse=True):
            with open(f, "r") as file:
                data = json.load(file)
                proposals.append(ImprovementProposal.from_dict(data))
        return proposals