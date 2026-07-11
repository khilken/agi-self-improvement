"""
Advanced Coding Agent
=====================

Read-only architecture-aware coding analyzer. It returns concrete inspection
metadata and a safe implementation checklist rather than fabricated edits.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("AdvancedCodingAgent")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
            "large_scale_refactoring",
        ]

    def inspect(self, context: dict) -> dict:
        task_type = context.get("type", "general")
        files = context.get("files", []) or []
        inspected = []
        for item in files[:20]:
            path = (PROJECT_ROOT / item).resolve()
            try:
                rel = path.relative_to(PROJECT_ROOT)
            except ValueError:
                inspected.append({"file": item, "status": "rejected_outside_project"})
                continue
            if not path.exists():
                inspected.append({"file": str(rel), "status": "missing"})
                continue
            if path.is_file():
                text = path.read_text(errors="replace")
                inspected.append({
                    "file": str(rel),
                    "status": "inspected",
                    "lines": text.count("\n") + (1 if text else 0),
                    "has_tests_hint": "test" in path.name.lower() or "tests" in path.parts,
                })

        return {
            "status": "analysis_only",
            "type": task_type,
            "files_inspected": inspected,
            "tests_written": 0,
            "files_modified": [],
            "checklist": [
                "Confirm scope and target files.",
                "Write or update regression tests first.",
                "Patch the smallest safe surface area.",
                "Run scripts/run_tests.py before reporting success.",
            ],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        logger.info("AdvancedCodingAgent received: %s", context.get("type", "general"))
        result = self.inspect(context)
        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(AdvancedCodingAgent())
