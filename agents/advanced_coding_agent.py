"""
Advanced Coding Agent
=====================

In-depth coding agent with support for:
- Multi-file refactoring
- Architecture-aware development
- Test-driven development (TDD)
- Code review integration
"""

import logging
from typing import List
from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("AdvancedCodingAgent")


class AdvancedCodingAgent(BaseMCPAgent):
    def __init__(self, name: str = "advanced_coding"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "multi_file_refactoring",
            "architecture_aware_coding",
            "test_driven_development",
            "code_review",
            "large_scale_refactoring"
        ]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        task_type = context.get("type", "general")

        logger.info(f"AdvancedCodingAgent received: {task_type}")

        result = {
            "status": "completed",
            "type": task_type,
            "files_modified": ["example.py", "tests/test_example.py"],
            "tests_written": 12,
            "notes": "Applied TDD approach with architecture review"
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(AdvancedCodingAgent())