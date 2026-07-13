"""
RAGFlow Agent
=============

Hermes MCP wrapper for infiniflow/ragflow.

RAGFlow is managed as an external Docker/Python/Go/Node RAG platform through
scripts/ragflow_manage.py. Hermes exposes source status, diagnostics,
Hermes-local Docker Compose rendering/validation, and explicit start/stop or
frontend build operations without importing RAGFlow into Hermes' Python runtime.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MCPMessage, MessageType
from scripts import ragflow_manage

logger = logging.getLogger("RAGFlowAgent")


class RAGFlowAgent(BaseMCPAgent):
    def __init__(self, name: str = "ragflow"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "ragflow",
            "rag_flow",
            "retrieval_augmented_generation",
            "rag_engine",
            "document_understanding",
            "ragflow_status",
            "ragflow_doctor",
            "ragflow_render_config",
            "ragflow_compose_config",
            "ragflow_up",
            "ragflow_down",
            "ragflow_wait_ready",
            "ragflow_web_setup",
            "ragflow_web_build",
        ]

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")
        timeout = int(context.get("timeout", 900)) if context else 900

        if task_l in {"status", "ragflow_status", "rag_flow_status"}:
            return {"status": "completed", "action": "status", "result": ragflow_manage.status()}

        if task_l in {"doctor", "ragflow_doctor", "rag_flow_doctor"}:
            return {"status": "completed", "action": "doctor", "result": ragflow_manage.doctor()}

        if task_l in {"render_config", "ragflow_render_config", "rag_flow_render_config"}:
            result = ragflow_manage.render_config()
            return {"status": "completed" if result.get("ok") else "failed", "action": "render_config", "result": result}

        if task_l in {"compose_config", "ragflow_compose_config", "rag_flow_compose_config"}:
            result = ragflow_manage.compose_config(timeout=int(context.get("timeout", 120)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "compose_config", "result": result}

        if task_l in {"up", "start", "ragflow_up", "ragflow_start"}:
            result = ragflow_manage.up(timeout=int(context.get("timeout", 1200)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "up", "result": result}

        if task_l in {"down", "stop", "ragflow_down", "ragflow_stop"}:
            result = ragflow_manage.down(timeout=int(context.get("timeout", 180)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "down", "result": result}

        if task_l in {"wait_ready", "ragflow_wait_ready", "rag_flow_wait_ready"}:
            result = ragflow_manage.wait_ready(timeout=int(context.get("timeout", 300)))
            return {"status": "completed" if result.get("ok") else "failed", "action": "wait_ready", "result": result}

        if task_l in {"web_setup", "ragflow_web_setup", "rag_flow_web_setup"}:
            result = ragflow_manage.web_setup(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "web_setup", "result": result}

        if task_l in {"web_build", "ragflow_web_build", "rag_flow_web_build"}:
            result = ragflow_manage.web_build(timeout=timeout)
            return {"status": "completed" if result.get("ok") else "failed", "action": "web_build", "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported RAGFlow task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "render_config", "compose_config", "up", "down", "wait_ready", "web_setup", "web_build"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("RAGFlow handling task_type=%s", task_type)
        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external runtime
            logger.exception("RAGFlow task failed")
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

    run_agent(RAGFlowAgent())
