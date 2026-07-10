"""
Knowledge Curator Agent (Improved)
==================================

Handles ingestion, deduplication, and linking of knowledge across Hermes.
"""

import logging
import hashlib
from typing import List, Dict, Any
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("KnowledgeCuratorAgent")


class KnowledgeCuratorAgent(BaseMCPAgent):
    def __init__(self, name: str = "knowledge_curator"):
        super().__init__(name=name)
        self.knowledge_base: Dict[str, Dict] = {}  # Simple in-memory store
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "knowledge_ingestion",
            "deduplication",
            "knowledge_linking",
            "knowledge_retrieval"
        ]

    def _generate_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        action = context.get("action", "ingest")
        data = context.get("data", {})

        logger.info(f"KnowledgeCurator received action: {action}")

        if action == "ingest":
            result = self._ingest(data)
        elif action == "deduplicate":
            result = self._deduplicate()
        elif action == "retrieve":
            result = self._retrieve(data.get("query", ""))
        else:
            result = {"status": "unknown_action"}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _ingest(self, data: Dict) -> Dict:
        content = str(data)
        h = self._generate_hash(content)
        if h not in self.knowledge_base:
            self.knowledge_base[h] = data
            return {"status": "ingested", "hash": h}
        return {"status": "duplicate", "hash": h}

    def _deduplicate(self) -> Dict:
        before = len(self.knowledge_base)
        # Simple dedup logic (already handled in ingest)
        after = len(self.knowledge_base)
        return {"status": "completed", "before": before, "after": after}

    def _retrieve(self, query: str) -> Dict:
        results = []
        for h, item in self.knowledge_base.items():
            if query.lower() in str(item).lower():
                results.append(item)
        return {"status": "completed", "results": results[:5]}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(KnowledgeCuratorAgent())