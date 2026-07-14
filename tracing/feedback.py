"""
Structured Human Feedback System
================================

Allows users to rate outputs and feed feedback back into the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import json
from pathlib import Path
import uuid


@dataclass
class Feedback:
    id: str
    trace_id: str
    rating: int               # 1-5
    comment: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    used_for_improvement: bool = False

    def to_dict(self):
        return {
            "id": self.id,
            "trace_id": self.trace_id,
            "rating": self.rating,
            "comment": self.comment,
            "timestamp": self.timestamp,
            "used_for_improvement": self.used_for_improvement
        }


class FeedbackStore:
    def __init__(self, storage_dir: str = "logs/feedback"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.storage_dir / "feedback.jsonl"

    def record(self, trace_id: str, rating: int, comment: str = "") -> Feedback:
        fb = Feedback(
            id=str(uuid.uuid4()),
            trace_id=trace_id,
            rating=rating,
            comment=comment
        )
        with open(self.file, "a") as f:
            f.write(json.dumps(fb.to_dict()) + "\n")
        return fb

    def get_by_trace(self, trace_id: str) -> List[Feedback]:
        results: List[Feedback] = []
        if not self.file.exists():
            return results
        with open(self.file, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data["trace_id"] == trace_id:
                        results.append(Feedback(**data))
        return results

    def get_all(self) -> List[Feedback]:
        results: List[Feedback] = []
        if not self.file.exists():
            return results
        with open(self.file, "r") as f:
            for line in f:
                if line.strip():
                    results.append(Feedback(**json.loads(line)))
        return results