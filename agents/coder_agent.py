"""
Coder Sub-Agent for Hermes
==========================

Conservative MCP coding helper. It analyzes requested files and returns a concrete
implementation plan; it does not fabricate generated code or claim file edits.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

try:
    from tasks.task_queue import complete_task, fail_task
    TASK_QUEUE_AVAILABLE = True
except ImportError:
    TASK_QUEUE_AVAILABLE = False

    def complete_task(task_id: str, result: dict[str, Any] | None = None) -> bool:
        return False

    def fail_task(task_id: str, error: str) -> bool:
        return False

logger = logging.getLogger("CoderAgent")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CoderAgent(BaseMCPAgent):
    """Sub-agent specialized in software development and coding task analysis."""

    def __init__(self, name: str = "coder"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "code_generation",
            "refactoring",
            "debugging",
            "test_writing",
            "architecture_review",
        ]

    def analyze_request(self, task_type: str, context: dict) -> dict:
        description = context.get("description", "")
        files = context.get("files", []) or context.get("file_paths", []) or []
        inspected = []
        missing = []

        for file_name in files[:10]:
            path = (PROJECT_ROOT / file_name).resolve()
            try:
                path.relative_to(PROJECT_ROOT)
            except ValueError:
                missing.append({"file": file_name, "reason": "outside project root"})
                continue
            if not path.exists():
                missing.append({"file": file_name, "reason": "not found"})
                continue
            if path.is_file():
                text = path.read_text(errors="replace")
                inspected.append({
                    "file": str(path.relative_to(PROJECT_ROOT)),
                    "lines": text.count("\n") + (1 if text else 0),
                    "bytes": len(text.encode()),
                })

        recommendations = []
        if not description:
            recommendations.append("Provide a concrete description before code changes are attempted.")
        if files and missing:
            recommendations.append("Resolve missing/out-of-root file paths before editing.")
        if inspected:
            recommendations.append("Create or update tests before applying code changes.")
        else:
            recommendations.append("No files inspected; this is analysis-only and no code was generated.")

        return {
            "status": "analysis_only",
            "task_type": task_type,
            "description": description,
            "files_inspected": inspected,
            "missing_files": missing,
            "recommendations": recommendations,
            "files_modified": [],
            "code_generated": None,
        }

    def handle_task_request(self, msg: MCPMessage):
        task_type = msg.payload.get("task_type", "code")
        context = msg.payload.get("context", {})
        logger.info("Coder received task: %s", task_type)

        try:
            result = self.analyze_request(task_type, context)
            task_id = msg.payload.get("task_id")
            if TASK_QUEUE_AVAILABLE and task_id:
                complete_task(str(task_id), result)
        except Exception as exc:
            logger.exception("Coder task failed")
            result = {"status": "failed", "error": str(exc), "files_modified": []}
            task_id = msg.payload.get("task_id")
            if TASK_QUEUE_AVAILABLE and task_id:
                fail_task(str(task_id), str(exc))

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(CoderAgent())
