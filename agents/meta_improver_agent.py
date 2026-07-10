"""
Meta-Improver Agent for Hermes (Structured Proposals)
=====================================================

Generates high-quality, structured improvement proposals following
2026 best practices (Hyperagents / Darwin Gödel Machine patterns).
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer
from tracing.proposal import ImprovementProposal, ProposalType, RiskLevel, ProposalStore

logger = logging.getLogger("MetaImproverAgent")


class MetaImproverAgent(BaseMCPAgent):
    def __init__(self, name: str = "meta_improver"):
        super().__init__(name=name)
        self.proposal_store = ProposalStore()
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
            result = self._analyze_and_generate_proposals()
        else:
            result = {"status": "unknown_task_type"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _analyze_and_generate_proposals(self) -> Dict[str, Any]:
        traces = tracer.get_recent_traces(limit=100)

        if not traces:
            return {"status": "no_traces"}

        low_score = [t for t in traces if t.evaluation_score and t.evaluation_score < 0.6]
        errors = [t for t in traces if t.error]

        patterns = defaultdict(int)
        for t in low_score:
            if t.evaluation_feedback:
                patterns[t.evaluation_feedback] += 1

        proposals: List[ImprovementProposal] = []

        # High-impact proposal: Add reflection step
        if len(low_score) > 5:
            proposal = ImprovementProposal(
                id=str(uuid.uuid4()),
                type=ProposalType.PROCESS_IMPROVEMENT,
                title="Add Evaluator step before final delivery",
                description="Route all significant outputs through the EvaluatorAgent for scoring and feedback before returning to the user.",
                reason="A large number of outputs are receiving low evaluation scores (<0.6). Adding a reflection step can significantly improve quality.",
                risk_level=RiskLevel.LOW,
                estimated_impact="Significant improvement in output quality",
                priority="high"
            )
            self.proposal_store.save(proposal)
            proposals.append(proposal)

        # Code improvement proposal
        if len(errors) > 3:
            proposal = ImprovementProposal(
                id=str(uuid.uuid4()),
                type=ProposalType.CODE_EDIT,
                title="Improve error handling across agents",
                description="Add better try/except blocks and fallback logic in Researcher and Coder agents.",
                reason="Multiple errors detected in recent traces. Improved error handling will reduce failure rate.",
                target_file="agents/researcher_agent.py",
                risk_level=RiskLevel.MEDIUM,
                estimated_impact="Reduced failure rate",
                priority="medium"
            )
            self.proposal_store.save(proposal)
            proposals.append(proposal)

        return {
            "status": "completed",
            "proposals_generated": len(proposals),
            "proposals": [p.to_dict() for p in proposals],
            "stats": {
                "total_traces": len(traces),
                "low_score": len(low_score),
                "errors": len(errors)
            }
        }