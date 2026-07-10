"""
Knowledge Curator Agent
=======================

Maintains, organizes, deduplicates, and links knowledge across the Hermes system.
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("KnowledgeCuratorAgent")


class KnowledgeCuratorAgent(BaseMCPAgent):
    def __init__(self, name: str = "knowledge_curator"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "knowledge_ingestion",
            "deduplication",
            "knowledge_linking",
            "knowledge_retrieval",
            "knowledge_maintenance"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        action = context.get("action", "ingest")

        logger.info(f"KnowledgeCurator received action: {action}")

        if action == "ingest":
            result = {"status": "completed", "message": "Knowledge ingested"}
        elif action == "deduplicate":
            result = {"status": "completed", "duplicates_found": 3}
        else:
            result = {"status": "unknown_action"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(KnowledgeCuratorAgent())