"""
Project Nomad Agent
===================

Hermes MCP wrapper for Project N.O.M.A.D. (Node for Offline Media, Archives, and Data).

Project Nomad is managed as an external Docker/Node subsystem through
scripts/project_nomad_manage.py. Hermes exposes status, diagnostics, compose
rendering, validation, and explicit start/stop operations without running the
upstream sudo installer or importing the Node application into Hermes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MCPMessage, MessageType
from scripts import project_nomad_manage

logger = logging.getLogger("ProjectNomadAgent")


class ProjectNomadAgent(BaseMCPAgent):
    def __init__(self, name: str = "project_nomad"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "project_nomad",
            "offline_knowledge_server",
            "offline_media_archives_data",
            "offline_ai_server",
            "nomad_status",
            "nomad_doctor",
            "nomad_render_compose",
            "nomad_compose_config",
            "nomad_setup",
            "nomad_build",
            "nomad_up",
            "nomad_down",
            "nomad_wait_ready",
        ]

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")

        if task_l in {"status", "project_nomad_status", "nomad_status"}:
            return {"status": "completed", "action": "status", "result": project_nomad_manage.status()}

        if task_l in {"doctor", "project_nomad_doctor", "nomad_doctor"}:
            return {"status": "completed", "action": "doctor", "result": project_nomad_manage.doctor()}

        if task_l in {"render_compose", "project_nomad_render_compose", "nomad_render_compose"}:
            result = project_nomad_manage.render_compose()
            return {"status": "completed" if result.get("ok") else "failed", "action": "render_compose", "result": result}

        if task_l in {"compose_config", "project_nomad_compose_config", "nomad_compose_config"}:
            result = project_nomad_manage.compose_config(timeout=int(context.get("timeout", 60)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "compose_config", "result": result}

        if task_l in {"setup", "project_nomad_setup", "nomad_setup"}:
            result = project_nomad_manage.npm_setup(timeout=int(context.get("timeout", 900)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "setup", "result": result}

        if task_l in {"build", "project_nomad_build", "nomad_build"}:
            result = project_nomad_manage.npm_build(timeout=int(context.get("timeout", 900)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "build", "result": result}

        if task_l in {"up", "start", "project_nomad_up", "nomad_up"}:
            result = project_nomad_manage.up(timeout=int(context.get("timeout", 600)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "up", "result": result}

        if task_l in {"down", "stop", "project_nomad_down", "nomad_down"}:
            result = project_nomad_manage.down(timeout=int(context.get("timeout", 120)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "down", "result": result}

        if task_l in {"wait_ready", "project_nomad_wait_ready", "nomad_wait_ready"}:
            result = project_nomad_manage.wait_ready(timeout=int(context.get("timeout", 120)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "wait_ready", "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported Project Nomad task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "render_compose", "compose_config", "setup", "build", "up", "down", "wait_ready"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("Project Nomad handling task_type=%s", task_type)
        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external runtime
            logger.exception("Project Nomad task failed")
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

    run_agent(ProjectNomadAgent())
