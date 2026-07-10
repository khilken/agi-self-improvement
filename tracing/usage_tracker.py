"""
Usage & Cost Tracking System
============================

Tracks token usage and estimated costs across agents.
Can trigger alerts when thresholds are exceeded.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class UsageRecord:
    timestamp: str
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost": self.estimated_cost
        }


class UsageTracker:
    def __init__(self, storage_dir: str = "logs/usage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.storage_dir / "usage.jsonl"

    def record(self, agent: str, model: str, input_tokens: int, output_tokens: int, cost: float):
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost
        )
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def get_daily_total(self) -> Dict:
        today = datetime.now().date().isoformat()
        total_tokens = 0
        total_cost = 0.0

        if not self.log_file.exists():
            return {"tokens": 0, "cost": 0.0}

        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data["timestamp"].startswith(today):
                        total_tokens += data["input_tokens"] + data["output_tokens"]
                        total_cost += data["estimated_cost"]

        return {"tokens": total_tokens, "cost": round(total_cost, 4)}

    def check_alerts(self, token_limit: int = 100000, cost_limit: float = 10.0) -> List[str]:
        stats = self.get_daily_total()
        alerts = []
        if stats["tokens"] > token_limit:
            alerts.append(f"Token usage exceeded: {stats['tokens']}/{token_limit}")
        if stats["cost"] > cost_limit:
            alerts.append(f"Cost exceeded: ${stats['cost']}/${cost_limit}")
        return alerts