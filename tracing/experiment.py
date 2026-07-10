"""
Experiment Tracking System
==========================

Tracks A/B tests and improvement experiments with results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
from pathlib import Path
import uuid


@dataclass
class Experiment:
    id: str
    name: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    winner: Optional[str] = None
    confidence: Optional[float] = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    notes: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "winner": self.winner,
            "confidence": self.confidence,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "notes": self.notes
        }


class ExperimentStore:
    def __init__(self, storage_dir: str = "logs/experiments"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, variant_a: Dict, variant_b: Dict) -> Experiment:
        exp = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            variant_a=variant_a,
            variant_b=variant_b
        )
        self._save(exp)
        return exp

    def record_result(self, exp_id: str, winner: str, confidence: float, notes: str = ""):
        exp = self.load(exp_id)
        if exp:
            exp.winner = winner
            exp.confidence = confidence
            exp.completed_at = datetime.now().isoformat()
            exp.notes = notes
            self._save(exp)

    def _save(self, exp: Experiment):
        with open(self.storage_dir / f"{exp.id}.json", "w") as f:
            json.dump(exp.to_dict(), f, indent=2)

    def load(self, exp_id: str) -> Optional[Experiment]:
        path = self.storage_dir / f"{exp_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return Experiment(**data)

    def list_all(self) -> List[Experiment]:
        exps = []
        for f in sorted(self.storage_dir.glob("*.json"), reverse=True):
            with open(f) as file:
                data = json.load(file)
                exps.append(Experiment(**data))
        return exps