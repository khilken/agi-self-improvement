"""
Awesome LLM Apps Agent
======================

Hermes MCP wrapper for Shubham Saboo's awesome-llm-apps template collection.

The upstream repo is a cookbook of many independent projects. This agent exposes
catalog/search/show/setup/run operations while preserving process and dependency
boundaries around each template.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MCPMessage, MessageType
from scripts import awesome_llm_apps_manage

logger = logging.getLogger("AwesomeLLMAppsAgent")


class AwesomeLLMAppsAgent(BaseMCPAgent):
    def __init__(self, name: str = "awesome_llm_apps"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "awesome_llm_apps",
            "llm_app_templates",
            "agent_template_catalog",
            "awesome_llm_apps_status",
            "awesome_llm_apps_doctor",
            "awesome_llm_apps_list",
            "awesome_llm_apps_show",
            "awesome_llm_apps_setup",
            "awesome_llm_apps_run",
        ]

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")

        if task_l in {"status", "awesome_llm_apps_status"}:
            return {"status": "completed", "action": "status", "result": awesome_llm_apps_manage.status()}

        if task_l in {"doctor", "awesome_llm_apps_doctor"}:
            return {"status": "completed", "action": "doctor", "result": awesome_llm_apps_manage.doctor()}

        if task_l in {"list", "catalog", "search", "awesome_llm_apps_list"}:
            result = awesome_llm_apps_manage.list_templates(
                category=context.get("category"),
                query=context.get("query") or context.get("q"),
                limit=int(context.get("limit", 50)),
            )
            return {"status": "completed", "action": "list", "result": result}

        if task_l in {"show", "inspect", "awesome_llm_apps_show"}:
            template = str(context.get("template") or context.get("id") or context.get("path") or "").strip()
            if not template:
                return {"status": "failed", "action": "show", "error": "Missing template/id/path in context"}
            try:
                result = awesome_llm_apps_manage.show(template)
            except KeyError as exc:
                return {"status": "failed", "action": "show", "error": str(exc)}
            return {"status": "completed", "action": "show", "result": result}

        if task_l in {"setup", "awesome_llm_apps_setup"}:
            template = str(context.get("template") or context.get("id") or context.get("path") or "").strip()
            if not template:
                return {"status": "failed", "action": "setup", "error": "Missing template/id/path in context"}
            try:
                result = awesome_llm_apps_manage.setup(
                    template,
                    timeout=int(context.get("timeout", 900)),
                    node=bool(context.get("node", True)),
                    python=bool(context.get("python", True)),
                )
            except KeyError as exc:
                return {"status": "failed", "action": "setup", "error": str(exc)}
            return {"status": "completed" if result.get("ok") else "failed", "action": "setup", "result": result}

        if task_l in {"run", "launch", "awesome_llm_apps_run"}:
            template = str(context.get("template") or context.get("id") or context.get("path") or "").strip()
            if not template:
                return {"status": "failed", "action": "run", "error": "Missing template/id/path in context"}
            try:
                result = awesome_llm_apps_manage.run_template(
                    template,
                    launcher=context.get("launcher"),
                    args=context.get("args", []),
                    timeout=int(context.get("timeout", 300)),
                )
            except KeyError as exc:
                return {"status": "failed", "action": "run", "error": str(exc)}
            return {"status": "completed" if result.get("ok") else "failed", "action": "run", "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported awesome-llm-apps task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "list", "show", "setup", "run"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("awesome-llm-apps handling task_type=%s", task_type)
        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external cookbook
            logger.exception("awesome-llm-apps task failed")
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

    run_agent(AwesomeLLMAppsAgent())
