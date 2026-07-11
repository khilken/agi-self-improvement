"""
Comprehensive Debugging & Testing Agent
=======================================

Runs real local verification commands and summarizes evidence. It does not claim
coverage increases or fixes unless backed by command output.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("ComprehensiveDebugTestingAgent")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ComprehensiveDebugTestingAgent(BaseMCPAgent):
    def __init__(self, name: str = "comprehensive_debug_testing"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "test_generation",
            "coverage_analysis",
            "root_cause_analysis",
            "safe_auto_fix",
            "regression_detection",
        ]

    def run_checks(self, focus: str = "general") -> dict:
        commands = [
            [sys.executable, "scripts/run_tests.py", "--no-pytest"],
        ]
        results = []
        for command in commands:
            proc = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                timeout=240,
                env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
            )
            output = (proc.stdout + proc.stderr).splitlines()
            results.append({
                "command": " ".join(command),
                "exit_code": proc.returncode,
                "tail": output[-40:],
            })
        passed = all(r["exit_code"] == 0 for r in results)
        return {
            "status": "completed" if passed else "failed",
            "focus": focus,
            "checks": results,
            "tests_generated": 0,
            "coverage_increase": None,
            "fixes_applied": 0,
            "notes": "Real verification run completed; no automatic source edits performed.",
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        focus = context.get("focus", "general")
        logger.info("ComprehensiveDebugTesting received focus: %s", focus)
        result = self.run_checks(focus)
        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(ComprehensiveDebugTestingAgent())
