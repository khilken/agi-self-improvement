"""
Example Sub-Agent: Researcher
=============================

Minimal MCP researcher example that produces evidence-based local summaries.
It avoids fabricated sources/results; callers can pass sources/snippets in the
message context and the agent will synthesize from only that provided evidence.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.protocol import BaseMCPAgent, MessageType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ExampleResearcherAgent")


class ResearcherAgent(BaseMCPAgent):
    def get_capabilities(self):
        return [
            "evidence_synthesis",
            "source_evaluation",
            "research_planning",
        ]

    def handle_task_request(self, msg: "MCPMessage"):
        task = msg.payload.get("task") or msg.payload.get("task_type", "research")
        context: dict[str, Any] = msg.payload.get("context", {}) or {}
        sources = context.get("sources", []) or []
        notes = context.get("notes") or context.get("snippets") or []
        if isinstance(notes, str):
            notes = [notes]

        logger.info("Received research task: %s", task)

        summary_parts = []
        if notes:
            summary_parts.append("Provided evidence:\n" + "\n".join(f"- {str(n)[:300]}" for n in notes[:8]))
        else:
            summary_parts.append("No source snippets were provided, so this example agent cannot claim factual findings.")

        result = {
            "task": task,
            "summary": "\n".join(summary_parts),
            "sources": [str(src) for src in sources],
            "confidence": 0.75 if notes else 0.2,
            "next_suggested_actions": [
                "Provide URLs/snippets or delegate to a real web-search-capable agent.",
                "Ask EvaluatorAgent to score the resulting evidence quality.",
            ],
            "fabricated": False,
        }

        self.mcp.report_result(
            to_agent=msg.from_agent,
            correlation_id=msg.correlation_id,
            result=result,
            success=True,
        )

        if "self_improving" in str(task).lower():
            self.mcp.propose_self_improvement(
                proposal="Connect example researcher to a real web/search tool adapter",
                rationale="The example agent currently only synthesizes provided evidence, by design.",
                expected_impact="Higher quality research while preserving no-fabrication behavior",
            )

    def run(self):
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)
        super().run_loop()


if __name__ == "__main__":
    agent = ResearcherAgent(name="researcher")
    print("Starting example Researcher sub-agent...")
    print("It listens for TASK_REQUEST messages via MCP and only summarizes provided evidence.")
    agent.run()
