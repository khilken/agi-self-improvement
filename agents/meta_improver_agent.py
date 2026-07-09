"""
Meta-Improver Agent for Hermes
==============================

Analyzes task traces, identifies failure patterns, and proposes
improvements to prompts, code, or agent behavior.
This is the core of recursive self-improvement.
"""

import logging
from typing import List, Dict, Any
from collections import defaultdict

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer

logger = logging.getLogger("MetaImproverAgent")


class MetaImproverAgent(BaseMCPAgent):
    """Agent that drives self-improvement by analyzing traces."""

    def __init__(self, name: str = "meta_improver"):
        super().__init__(name=name)
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
        context = msg.payload.get("context", {})

        logger.info(f"MetaImprover received task: {task_type}")

        if task_type == "analyze_traces":
            result = self._analyze_recent_traces()
        else:
            result = {"status": "unknown_task_type"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _analyze_recent_traces(self) -> Dict[str, Any]:
        traces = tracer.get_recent_traces(limit=100)

        if not traces:
            return {"status": "no_traces", "message": "No traces found yet."}

        # Analyze failure patterns
        low_score_traces = [t for t in traces if t.evaluation_score and t.evaluation_score < 0.6]
        error_traces = [t for t in traces if t.error]

        patterns = defaultdict(int)
        for t in low_score_traces:
            if t.evaluation_feedback:
                patterns[t.evaluation_feedback] += 1

        # Generate improvement proposals
        proposals = []
        if len(low_score_traces) > 5:
            proposals.append("Many outputs are receiving low scores. Consider adding an Evaluator step before final delivery.")
        if len(error_traces) > 3:
            proposals.append("Multiple errors detected. Review error handling in agents.")

        return {
            "status": "completed",
            "total_traces": len(traces),
            "low_score_count": len(low_score_traces),
            "error_count": len(error_traces),
            "common_feedback_patterns": dict(patterns),
            "improvement_proposals": proposals
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("MetaImproverAgent ready. Use HermesDispatcher to send tasks.")