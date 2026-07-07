"""
Example Sub-Agent: Researcher
Demonstrates how to build a specialized agent that speaks MCP and works under Hermes.

This agent could be expanded with real web_search, browse_page, and LLM summarization tools.
"""

import logging
from mcp.protocol import BaseMCPAgent, MessageType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResearcherAgent")


class ResearcherAgent(BaseMCPAgent):
    def get_capabilities(self):
        return [
            "web_research",
            "paper_summarization",
            "trend_analysis",
            "source_evaluation"
        ]

    def handle_task_request(self, msg: "MCPMessage"):
        task = msg.payload.get("task", "")
        context = msg.payload.get("context", {})

        logger.info(f"Received research task: {task}")

        # TODO: In real implementation, use tools here:
        # - web_search / browse_page
        # - Call local LLM (Ollama) for summarization
        # - Synthesize findings

        fake_result = {
            "task": task,
            "summary": f"Research summary for: {task}. Key findings: ... (placeholder)",
            "sources": ["https://arxiv.org/example1", "https://github.com/example"],
            "confidence": 0.85,
            "next_suggested_actions": [
                "Deep dive into paper X",
                "Compare with previous research on Y"
            ]
        }

        # Report back using correlation_id so Hermes can match the result
        self.mcp.report_result(
            to_agent=msg.from_agent,
            correlation_id=msg.correlation_id,
            result=fake_result,
            success=True
        )

        # Optionally propose a self-improvement
        if "self_improving" in task.lower():
            self.mcp.propose_self_improvement(
                proposal="Add native arXiv + Hugging Face paper ingestion tool to Researcher agent",
                rationale="Would significantly speed up self-improvement research loops",
                expected_impact="Higher quality and faster capability gap analysis"
            )

    def run(self):
        # Override to add custom handler registration if needed
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)
        super().run_loop()


if __name__ == "__main__":
    agent = ResearcherAgent(name="researcher")
    print("Starting example Researcher sub-agent...")
    print("It will listen for TASK_REQUEST messages via MCP.")
    agent.run()