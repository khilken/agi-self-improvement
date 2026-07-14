"""
Task Trace System for Hermes
============================

Structured logging of agent tasks for analysis, evaluation,
and self-improvement loops.
"""

import json
import time
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TaskTrace:
    trace_id: str
    task_type: str
    agent: str
    input_data: Dict[str, Any]
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    output_data: Optional[Dict[str, Any]] = None
    evaluation_score: Optional[float] = None
    evaluation_feedback: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    def duration(self) -> Optional[float]:
        if self.end_time:
            return self.end_time - self.start_time
        return None


class TaskTracer:
    def __init__(self, log_dir: str = "logs/traces"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_traces: Dict[str, TaskTrace] = {}

    def start_trace(
        self,
        task_type: str,
        agent: str,
        input_data: Dict[str, Any],
        metadata: Optional[Dict] = None,
    ) -> str:
        trace_id = str(uuid.uuid4())
        trace = TaskTrace(
            trace_id=trace_id,
            task_type=task_type,
            agent=agent,
            input_data=input_data,
            metadata=metadata or {},
        )
        self.current_traces[trace_id] = trace
        # Persist immediately for better observability
        self._save_trace(trace)
        return trace_id

    def end_trace(
        self,
        trace_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        if trace_id not in self.current_traces:
            return

        trace = self.current_traces[trace_id]
        trace.end_time = time.time()
        trace.output_data = output_data
        trace.error = error

        self._save_trace(trace)
        del self.current_traces[trace_id]

    def add_evaluation(
        self, trace_id: str, score: float, feedback: str
    ):
        if trace_id in self.current_traces:
            self.current_traces[trace_id].evaluation_score = score
            self.current_traces[trace_id].evaluation_feedback = feedback
        else:
            # Load from disk if already saved
            self._update_saved_trace(trace_id, score, feedback)

    def _save_trace(self, trace: TaskTrace):
        filename = f"{trace.trace_id}.json"
        filepath = self.log_dir / filename
        with open(filepath, "w") as f:
            json.dump(trace.to_dict(), f, indent=2)

    def _update_saved_trace(self, trace_id: str, score: float, feedback: str):
        filepath = self.log_dir / f"{trace_id}.json"
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
            data["evaluation_score"] = score
            data["evaluation_feedback"] = feedback
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)

    def get_recent_traces(self, limit: int = 50) -> List[TaskTrace]:
        files = sorted(self.log_dir.glob("*.json"), reverse=True)[:limit]
        traces = []
        for f in files:
            with open(f, "r") as file:
                data = json.load(file)
                traces.append(TaskTrace(**data))
        return traces


# Global tracer instance
tracer = TaskTracer()