"""
Automatic Debug + Log Analyzer Agent
====================================

Analyzes logs and reports concrete error evidence. It does not claim fixes were
applied unless another component actually applies them.
"""

from __future__ import annotations

import glob
import logging
import re
from collections import Counter
from pathlib import Path
from typing import List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage

logger = logging.getLogger("AutoDebugAgent")

ERROR_PATTERNS = [
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"\b(?:ERROR|CRITICAL|Exception|ImportError|ModuleNotFoundError|RuntimeError|SyntaxError)\b"),
]


class AutoDebugAgent(BaseMCPAgent):
    def __init__(self, name: str = "auto_debug"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "log_analysis",
            "error_detection",
            "automatic_fix_proposal",
            "safe_auto_fix",
        ]

    def analyze_logs(self, log_glob: str = "logs/*.log", max_lines_per_file: int = 400) -> dict:
        files = sorted(glob.glob(log_glob))
        findings = []
        error_counter: Counter[str] = Counter()

        for file_name in files:
            path = Path(file_name)
            try:
                lines = path.read_text(errors="replace").splitlines()[-max_lines_per_file:]
            except OSError as exc:
                findings.append({"file": str(path), "error": f"cannot read log: {exc}"})
                continue

            for idx, line in enumerate(lines, start=max(1, len(lines) - max_lines_per_file + 1)):
                if any(pattern.search(line) for pattern in ERROR_PATTERNS):
                    kind = self._classify(line)
                    error_counter[kind] += 1
                    findings.append({
                        "file": str(path),
                        "line": idx,
                        "kind": kind,
                        "text": line[-500:],
                    })

        proposals = self._propose_fixes(error_counter)
        return {
            "status": "completed",
            "files_scanned": len(files),
            "issues_found": len(findings),
            "findings": findings[:50],
            "fixes_applied": 0,
            "fixes_proposed": proposals,
        }

    def _classify(self, line: str) -> str:
        for key in ["ModuleNotFoundError", "ImportError", "SyntaxError", "RuntimeError", "Traceback", "ERROR", "CRITICAL"]:
            if key in line:
                return key
        return "error"

    def _propose_fixes(self, counts: Counter[str]) -> list[dict]:
        proposals = []
        if counts.get("ModuleNotFoundError") or counts.get("ImportError"):
            proposals.append({"issue": "missing_dependency_or_import", "fix": "install requirements.txt and verify PYTHONPATH=."})
        if counts.get("SyntaxError"):
            proposals.append({"issue": "syntax_error", "fix": "run scripts/run_tests.py and patch the reported file."})
        if counts.get("RuntimeError"):
            proposals.append({"issue": "runtime_error", "fix": "inspect traceback context and add regression test before patching."})
        return proposals

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        log_file = context.get("log_file", "logs/*.log")
        logger.info("AutoDebug analyzing: %s", log_file)

        result = self.analyze_logs(log_file)
        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent
    run_agent(AutoDebugAgent())
