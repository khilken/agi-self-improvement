"""
Example: MCP + Vector Memory Integration

Shows how a sub-agent (or Hermes itself) can:
1. Receive a task via MCP
2. Use Vector Memory to retrieve relevant past knowledge
3. Perform work
4. Store new findings back into Vector Memory
5. Report results via MCP (which Hermes can also store)

This pattern should become standard for all capable sub-agents.
"""

from mcp.protocol import MCPProtocol, MessageType, BaseMCPAgent
from vector_memory import VectorMemory
import logging

logger = logging.getLogger("IntegratedAgent")


class ResearchAgentWithMemory(BaseMCPAgent):
    def __init__(self, name: str = "researcher"):
        super().__init__(name=name)
        self.vm = VectorMemory()  # Shared long-term memory

    def get_capabilities(self):
        return ["web_research", "semantic_memory", "research_synthesis"]

    def handle_task_request(self, msg):
        task = msg.payload.get("task", "")
        context = msg.payload.get("context", {})

        # 1. Retrieve relevant past knowledge
        prior_knowledge = self.vm.get_relevant_context(
            query=task,
            n_results=5,
            filter={"project": context.get("project", "general")}
        )

        logger.info(f"Retrieved {len(prior_knowledge)} chars of prior context")

        # 2. Do the actual research work (placeholder - replace with real tools + LLM)
        research_result = f"Research result for: {task}\nPrior knowledge used: {prior_knowledge[:300]}..."

        # 3. Store the new finding
        self.vm.add_research_finding(
            content=research_result,
            project=context.get("project", "general"),
            source_url=context.get("source_url")
        )

        # 4. Report back via MCP
        self.mcp.report_result(
            to_agent=msg.from_agent,
            correlation_id=msg.correlation_id,
            result={
                "summary": research_result[:500],
                "stored_in_vector_memory": True,
                "prior_context_used": bool(prior_knowledge)
            }
        )

        # 5. Optionally propose improvement
        if "self-improving" in task.lower() or "agi" in task.lower():
            self.mcp.propose_self_improvement(
                proposal="Automatically consolidate vector memory entries older than 30 days into summaries",
                rationale="Reduces noise and improves retrieval quality over long time horizons",
                expected_impact="Better long-term reasoning and fewer duplicate research efforts"
            )


if __name__ == "__main__":
    agent = ResearchAgentWithMemory()
    print("Starting ResearchAgentWithMemory (MCP + Vector Memory)...")
    agent.mcp.register_handler(MessageType.TASK_REQUEST, agent.handle_task_request)
    agent.run_loop()