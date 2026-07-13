"""
Momo Agent
==========

Hermes MCP wrapper for the Momo self-hostable AI memory system.

Momo is integrated as an external Rust service through scripts/momo_manage.py.
Hermes talks to it via process and REST boundaries rather than importing Rust
internals into the Python process.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from scripts import momo_manage

logger = logging.getLogger("MomoAgent")


class MomoAgent(BaseMCPAgent):
    def __init__(self, name: str = "momo"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "momo",
            "ai_memory_system",
            "external_memory_service",
            "mcp_memory_server",
            "momo_status",
            "momo_doctor",
            "momo_build",
            "momo_health",
            "momo_document",
            "momo_documents",
            "momo_search",
            "momo_ingest",
        ]

    def inspect(self) -> Dict[str, Any]:
        return momo_manage.status()

    def diagnose(self) -> Dict[str, Any]:
        return momo_manage.doctor()

    def execute(self, task_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        task_l = (task_type or "status").lower().replace("-", "_")

        if task_l in {"status", "inspect", "momo_status"}:
            return {"status": "completed", "action": "status", "result": self.inspect()}

        if task_l in {"doctor", "diagnose", "momo_doctor"}:
            return {"status": "completed", "action": "doctor", "result": self.diagnose()}

        if task_l in {"health", "momo_health"}:
            return {"status": "completed", "action": "health", "result": momo_manage.health(timeout=int(context.get("timeout", 10)))}

        if task_l in {"build", "momo_build"}:
            result = momo_manage.build(
                release=not bool(context.get("debug", False)),
                timeout=int(context.get("timeout", 900)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "build", "result": result}

        if task_l in {"search", "recall", "momo_search"}:
            query = str(context.get("query") or context.get("q") or "").strip()
            if not query:
                return {"status": "failed", "action": "search", "error": "Missing query/q in context"}
            tags = context.get("container_tags") or context.get("containerTags")
            if isinstance(tags, str):
                tags = [tags]
            result = momo_manage.search(
                query=query,
                container_tags=tags,
                scope=str(context.get("scope", "hybrid")),
                limit=int(context.get("limit", 10)),
                timeout=int(context.get("timeout", 60)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "search", "result": result}

        if task_l in {"document", "create_document", "momo_document"}:
            text = str(context.get("text") or context.get("content") or "").strip()
            if not text:
                return {"status": "failed", "action": "document", "error": "Missing text/content in context"}
            result = momo_manage.create_document(
                content=text,
                container_tag=str(context.get("container_tag") or context.get("containerTag") or "hermes"),
                title=context.get("title"),
                custom_id=context.get("custom_id") or context.get("customId"),
                content_type=str(context.get("content_type") or context.get("contentType") or "text/plain"),
                extract_memories=bool(context.get("extract_memories") or context.get("extractMemories") or False),
                timeout=int(context.get("timeout", 60)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "document", "result": result}

        if task_l in {"documents", "list_documents", "momo_documents"}:
            tags = context.get("container_tags") or context.get("containerTags")
            if isinstance(tags, str):
                tags = [tags]
            result = momo_manage.list_documents(
                container_tags=tags,
                limit=int(context.get("limit", 20)),
                timeout=int(context.get("timeout", 30)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "documents", "result": result}

        if task_l in {"ingest", "memory", "save", "momo_ingest"}:
            text = str(context.get("text") or context.get("content") or context.get("message") or "").strip()
            messages = context.get("messages")
            if not messages:
                if not text:
                    return {"status": "failed", "action": "ingest", "error": "Missing text/content/message or messages in context"}
                messages = [{"role": "user", "content": text}]
            result = momo_manage.ingest_conversation(
                messages=messages,
                container_tag=str(context.get("container_tag") or context.get("containerTag") or "hermes"),
                timeout=int(context.get("timeout", 60)),
            )
            return {"status": "completed" if result.get("ok") else "failed", "action": "ingest", "result": result}

        return {
            "status": "failed",
            "error": f"Unsupported Momo task_type: {task_type}",
            "supported_task_types": ["status", "doctor", "health", "build", "document", "documents", "search", "ingest"],
        }

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {}) or {}
        task_type = msg.payload.get("task_type") or context.get("task_type") or "status"
        logger.info("Momo handling task_type=%s", task_type)

        try:
            result = self.execute(task_type, context)
        except Exception as exc:  # defensive boundary around external subsystem
            logger.exception("Momo task failed")
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

    run_agent(MomoAgent())
