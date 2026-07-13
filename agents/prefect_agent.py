"""
Prefect Agent
=============

Hermes MCP wrapper for Prefect workflow orchestration.

Prefect is managed as an external Python runtime in an isolated virtualenv under
~/.hermes/prefect. This wrapper exposes safe lifecycle, CLI, server, and smoke
operations without importing Prefect into Hermes' host runtime.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MCPMessage, MessageType
from scripts import prefect_manage

logger = logging.getLogger("PrefectAgent")


class PrefectAgent(BaseMCPAgent):
    def __init__(self, name: str = "prefect"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "prefect",
            "workflow_orchestration",
            "flow_orchestration",
            "prefect_status",
            "prefect_doctor",
            "prefect_setup",
            "prefect_cli",
            "prefect_smoke",
            "prefect_server",
            "prefect_wait_ready",
        ]

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")

        if task_l in {"status", "prefect_status"}:
            return {"status": "completed", "action": "status", "result": prefect_manage.status()}

        if task_l in {"doctor", "prefect_doctor"}:
            return {"status": "completed", "action": "doctor", "result": prefect_manage.doctor()}

        if task_l in {"setup", "prefect_setup"}:
            result = prefect_manage.setup(
                timeout=int(context.get("timeout", 1200)),
                editable=bool(context.get("editable", True)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "setup", "result": result}

        if task_l in {"cli", "prefect_cli"}:
            result = prefect_manage.cli(
                context.get("args", []),
                timeout=int(context.get("timeout", 180)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "cli", "result": result}

        if task_l in {"smoke", "prefect_smoke"}:
            result = prefect_manage.smoke(timeout=int(context.get("timeout", 180)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "smoke", "result": result}

        if task_l in {"server", "prefect_server"}:
            result = prefect_manage.server(timeout=int(context.get("timeout", 3600)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "server", "result": result}

        if task_l in {"wait_ready", "prefect_wait_ready"}:
            result = prefect_manage.wait_ready(timeout=int(context.get("timeout", 60)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "wait_ready", "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported Prefect task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "setup", "cli", "smoke", "server", "wait_ready"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("Prefect handling task_type=%s", task_type)
        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external runtime
            logger.exception("Prefect task failed")
            result = {"status": "failed", "error": str(exc), "action": task_type}

        self.mcp.send(
            to_agent=msg.from_agent,
            msg_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from agents.base_runner import run_agent

    run_agent(PrefectAgent())
