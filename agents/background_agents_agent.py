"""
Background Agents Agent
=======================

Hermes MCP wrapper for ColeMurray/background-agents, also known as Open-Inspect.

Open-Inspect is managed as an external TypeScript/Python monorepo through
scripts/background_agents_manage.py. Hermes exposes source status, diagnostics,
and explicit setup/build/test/web operations without deploying cloud
infrastructure or importing the external app into Hermes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MCPMessage, MessageType
from scripts import background_agents_manage

logger = logging.getLogger("BackgroundAgentsAgent")


class BackgroundAgentsAgent(BaseMCPAgent):
    def __init__(self, name: str = "background_agents"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "background_agents",
            "open_inspect",
            "background_coding_agents",
            "cloud_coding_agents",
            "coding_agent_sandboxes",
            "background_agents_status",
            "background_agents_doctor",
            "background_agents_setup",
            "background_agents_build",
            "background_agents_typecheck",
            "background_agents_test",
            "background_agents_web_dev",
            "background_agents_web_build",
            "background_agents_shared_build",
        ]

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")
        timeout = int(context.get("timeout", 900)) if context else 900

        if task_l in {"status", "background_agents_status", "open_inspect_status"}:
            return {"status": "completed", "action": "status", "result": background_agents_manage.status()}

        if task_l in {"doctor", "background_agents_doctor", "open_inspect_doctor"}:
            return {"status": "completed", "action": "doctor", "result": background_agents_manage.doctor()}

        if task_l in {"setup", "background_agents_setup", "open_inspect_setup"}:
            result = background_agents_manage.setup(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "setup", "result": result}

        if task_l in {"build", "background_agents_build", "open_inspect_build"}:
            result = background_agents_manage.build(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "build", "result": result}

        if task_l in {"typecheck", "background_agents_typecheck", "open_inspect_typecheck"}:
            result = background_agents_manage.typecheck(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "typecheck", "result": result}

        if task_l in {"test", "background_agents_test", "open_inspect_test"}:
            result = background_agents_manage.test(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "test", "result": result}

        if task_l in {"web_dev", "background_agents_web_dev", "open_inspect_web_dev"}:
            result = background_agents_manage.web_dev(timeout=int(context.get("timeout", 3600)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "web_dev", "result": result}

        if task_l in {"web_build", "background_agents_web_build", "open_inspect_web_build"}:
            result = background_agents_manage.web_build(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "web_build", "result": result}

        if task_l in {"shared_build", "background_agents_shared_build", "open_inspect_shared_build"}:
            result = background_agents_manage.shared_build(timeout=int(context.get("timeout", 300)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "shared_build", "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported Background Agents task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "setup", "build", "typecheck", "test", "web_dev", "web_build", "shared_build"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("Background Agents handling task_type=%s", task_type)
        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external runtime
            logger.exception("Background Agents task failed")
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

    run_agent(BackgroundAgentsAgent())
