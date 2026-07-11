"""
Example: MCP + Vector Memory Integration
========================================

Shows how a sub-agent can retrieve relevant long-term memory, synthesize from
provided evidence, store the resulting finding, and report it through MCP.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.protocol import MessageType, BaseMCPAgent
from vector_memory import VectorMemory

logger = logging.getLogger("IntegratedAgent")


class ResearchAgentWithMemory(BaseMCPAgent):
    def __init__(self, name: str = "researcher"):
        super().__init__(name=name)
        self.vm = VectorMemory()

    def get_capabilities(self):
        return ["evidence_synthesis", "semantic_memory", "research_synthesis"]

    def handle_task_request(self, msg):
        task = msg.payload.get("task") or msg.payload.get("task_type", "research")
        context: dict[str, Any] = msg.payload.get("context", {}) or {}
        project = context.get("project", "general")

        prior_knowledge = self.vm.get_relevant_context(
            query=str(task),
            n_results=5,
            filter={"project": project},
        )
        logger.info("Retrieved %s chars of prior context", len(prior_knowledge))

        evidence = context.get("evidence") or context.get("notes") or []
        if isinstance(evidence, str):
            evidence = [evidence]

        if evidence:
            evidence_summary = "\n".join(f"- {str(item)[:500]}" for item in evidence[:10])
        else:
            evidence_summary = "No new external evidence supplied; result is based on prior vector memory only."

        research_result = (
            f"Task: {task}\n"
            f"Project: {project}\n\n"
            f"Evidence:\n{evidence_summary}\n\n"
            f"Prior knowledge excerpt:\n{prior_knowledge[:1200]}"
        )

        stored_id = self.vm.add_research_finding(
            content=research_result,
            project=project,
            source_url=context.get("source_url"),
        )

        self.mcp.report_result(
            to_agent=msg.from_agent,
            correlation_id=msg.correlation_id,
            result={
                "summary": research_result[:1000],
                "stored_in_vector_memory": bool(stored_id),
                "stored_id": stored_id,
                "prior_context_used": bool(prior_knowledge),
                "evidence_items_used": len(evidence),
                "fabricated": False,
            },
        )

        if "self-improving" in str(task).lower() or "agi" in str(task).lower():
            self.mcp.propose_self_improvement(
                proposal="Schedule periodic vector-memory consolidation and importance scoring",
                rationale="Keeps long-term retrieval compact, auditable, and high signal.",
                expected_impact="Better long-term reasoning and fewer duplicate research efforts",
            )


if __name__ == "__main__":
    agent = ResearchAgentWithMemory()
    print("Starting ResearchAgentWithMemory (MCP + Vector Memory)...")
    agent.mcp.register_handler(MessageType.TASK_REQUEST, agent.handle_task_request)
    agent.run_loop()
