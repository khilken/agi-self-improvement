"""
OpenCRABS Agent
===============

Hermes MCP wrapper for the OpenCRABS Rust agent runtime.

OpenCRABS is integrated as an external subsystem through scripts/opencrabs_manage.py,
not imported into the Python process. This preserves Hermes' Python runtime isolation
while allowing Hermes to inspect, build, run, and delegate to OpenCRABS when a binary
or Rust toolchain is available.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from scripts import opencrabs_manage

logger = logging.getLogger("OpenCrabsAgent")


class OpenCrabsAgent(BaseMCPAgent):
    def __init__(self, name: str = "opencrabs"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "opencrabs",
            "rust_agent_runtime",
            "a2a_gateway",
            "external_agent_runtime",
            "opencrabs_status",
            "opencrabs_doctor",
            "opencrabs_build",
            "opencrabs_run",
        ]

    def inspect(self) -> Dict[str, Any]:
        """Return non-mutating OpenCRABS integration status."""
        return opencrabs_manage.status()

    def diagnose(self) -> Dict[str, Any]:
        """Return non-mutating diagnostics with actionable setup guidance."""
        return opencrabs_manage.doctor()

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")

        if task_l in {"status", "inspect", "opencrabs_status"}:
            return {"status": "completed", "action": "status", "result": self.inspect()}

        if task_l in {"doctor", "diagnose", "opencrabs_doctor"}:
            return {"status": "completed", "action": "doctor", "result": self.diagnose()}

        if task_l in {"build", "opencrabs_build"}:
            result = opencrabs_manage.build(
                release=not bool(context.get("debug", False)),
                timeout=int(context.get("timeout", 600)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "build", "result": result}

        if task_l in {"run", "prompt", "opencrabs_run"}:
            prompt = str(context.get("prompt") or context.get("message") or context.get("query") or "").strip()
            if not prompt:
                return {"status": "failed", "action": "run", "error": "Missing prompt/message/query in context"}
            result = opencrabs_manage.run_prompt(
                prompt,
                auto_approve=bool(context.get("auto_approve", False)),
                fmt=str(context.get("format", "text")),
                timeout=int(context.get("timeout", 300)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "run", "result": result}

        if task_l in {"command", "cli"}:
            command = str(context.get("command", "status"))
            result = opencrabs_manage.passthrough(command, timeout=int(context.get("timeout", 120)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "command", "command": command, "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported OpenCRABS task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "build", "run", "command"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("OpenCRABS handling task_type=%s", task_type)

        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external subsystem
            logger.exception("OpenCRABS task failed")
            result = {"status": "failed", "error": str(exc), "action": task_type}

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent

    run_agent(OpenCrabsAgent())
