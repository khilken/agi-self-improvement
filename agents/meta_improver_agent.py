"""
Meta-Improver Agent for Hermes
==============================

Analyzes task traces and persists improvement proposals.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer

logger = logging.getLogger("MetaImproverAgent")


class MetaImproverAgent(BaseMCPAgent):
    def __init__(self, name: str = "meta_improver", proposals_dir: str = "logs/improvements"):
        super().__init__(name=name)
        self.proposals_dir = Path(proposals_dir)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "trace_analysis",
            "failure_pattern_detection",
            "improvement_proposal",
            "prompt_optimization"
        ]

    def handle_task_request(self, msg: MCPMessage):
        task_type = msg.payload.get("task_type", "analyze_traces")

        if task_type == "analyze_traces":
            result = self._analyze_and_persist()
        else:
            result = {"status": "unknown_task_type"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _analyze_and_persist(self) -> Dict[str, Any]:
        traces = tracer.get_recent_traces(limit=100)

        if not traces:
            return {"status": "no_traces"}

        low_score = [t for t in traces if t.evaluation_score and t.evaluation_score < 0.6]
        errors = [t for t in traces if t.error]

        patterns = defaultdict(int)
        for t in low_score:
            if t.evaluation_feedback:
                patterns[t.evaluation_feedback] += 1

        proposals = []
        if len(low_score) > 5:
            proposals.append({
                "type": "add_reflection",
                "description": "Add Evaluator step before final delivery",
                "priority": "high"
            })
        if len(errors) > 3:
            proposals.append({
                "type": "improve_error_handling",
                "description": "Strengthen error handling in agents",
                "priority": "medium"
            })

        # Persist proposals
        if proposals:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.proposals_dir / f"proposals_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "proposals": proposals,
                    "stats": {
                        "total_traces": len(traces),
                        "low_score": len(low_score),
                        "errors": len(errors)
                    }
                }, f, indent=2)

        return {
            "status": "completed",
            "proposals_generated": len(proposals),
            "proposals": proposals,
            "saved_to": str(self.proposals_dir)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("MetaImproverAgent ready.")