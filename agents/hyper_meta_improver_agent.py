"""
Hyper-Meta-Improver Agent
=========================

A self-referential meta-agent that can propose improvements to its own
improvement logic (metacognitive self-modification).

This is inspired by Meta's HyperAgents (2026) and the Darwin Gödel Machine.
"""

import logging
import uuid
from typing import List, Dict, Any
from collections import defaultdict

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer
from tracing.proposal import ImprovementProposal, ProposalType, RiskLevel, ProposalStore

logger = logging.getLogger("HyperMetaImproverAgent")


class HyperMetaImproverAgent(BaseMCPAgent):
    """
    A meta-agent that improves the Meta-Improver itself.
    It analyzes traces of the Meta-Improver's performance and proposes
    changes to its own analysis, proposal generation, or prompting strategy.
    """

    def __init__(self, name: str = "hyper_meta_improver"):
        super().__init__(name=name)
        self.proposal_store = ProposalStore()
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "metacognitive_analysis",
            "self_modification_proposal",
            "improvement_strategy_evolution",
            "meta_level_reflection"
        ]

    def handle_task_request(self, msg: MCPMessage):
        task_type = msg.payload.get("task_type", "analyze_meta_improver")

        if task_type == "analyze_meta_improver":
            result = self._analyze_own_performance()
        else:
            result = {"status": "unknown_task_type"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _analyze_own_performance(self) -> Dict[str, Any]:
        """
        Analyze traces where the Meta-Improver was involved and
        propose improvements to its own logic.
        """
        traces = tracer.get_recent_traces(limit=150)

        # Filter traces related to the Meta-Improver
        meta_traces = [
            t for t in traces 
            if "meta_improver" in str(t.agent).lower() or 
               "analyze_traces" in str(t.task_type).lower()
        ]

        if not meta_traces:
            return {"status": "no_meta_traces"}

        # Analyze patterns in Meta-Improver performance
        low_quality_proposals = [
            t for t in meta_traces 
            if t.evaluation_score and t.evaluation_score < 0.65
        ]

        proposals = []

        # Proposal 1: Improve proposal quality evaluation
        if len(low_quality_proposals) > 4:
            proposal = ImprovementProposal(
                id=str(uuid.uuid4()),
                type=ProposalType.CODE_EDIT,
                title="Enhance Meta-Improver proposal quality scoring",
                description="Add a secondary LLM judge step when generating proposals to filter low-quality suggestions before they reach the ApprovalGate.",
                reason=f"{len(low_quality_proposals)} proposals from the Meta-Improver received low scores. Adding an internal quality filter should reduce noise.",
                target_file="agents/meta_improver_agent.py",
                risk_level=RiskLevel.MEDIUM,
                estimated_impact="Higher quality proposals reaching human review",
                priority="high"
            )
            self.proposal_store.save(proposal)
            proposals.append(proposal)

        # Proposal 2: Improve trace analysis depth
        proposal2 = ImprovementProposal(
            id=str(uuid.uuid4()),
            type=ProposalType.PROCESS_IMPROVEMENT,
            title="Add few-shot examples to Meta-Improver prompting",
            description="Include 3-5 high-quality past proposals as few-shot examples when analyzing traces.",
            reason="Current Meta-Improver proposals sometimes lack specificity. Few-shot examples have shown strong improvements in other agents.",
            target_file="agents/meta_improver_agent.py",
            risk_level=RiskLevel.LOW,
            estimated_impact="More concrete and actionable proposals",
            priority="medium"
        )
        self.proposal_store.save(proposal2)
        proposals.append(proposal2)

        return {
            "status": "completed",
            "proposals_generated": len(proposals),
            "proposals": [p.to_dict() for p in proposals],
            "meta_traces_analyzed": len(meta_traces)
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent

    run_agent(HyperMetaImproverAgent())