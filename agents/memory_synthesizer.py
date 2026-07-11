"""
MemorySynthesizer Sub-Agent for Hermes
======================================

A specialized MCP-enabled sub-agent whose job is to maintain and improve
the long-term Vector Memory of the Hermes system.

Core Responsibilities:
- Periodic or on-demand memory consolidation
- Semantic deduplication and clustering
- Importance scoring and prioritization
- Creation of higher-level synthesized insights / summaries
- Archiving or soft-deletion of low-value / redundant memories
- Generating memory health reports and reflections

This agent is critical for turning raw accumulated knowledge into
high-quality, queryable, and compact long-term memory — a key requirement
for self-sustaining AGI.

It communicates exclusively via MCP and reads/writes to the shared VectorMemory.
"""

import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from vector_memory import VectorMemory

# Shared Task Queue support
try:
    from tasks.task_queue import (
        list_pending_tasks, claim_task, complete_task, fail_task
    )
    TASK_QUEUE_AVAILABLE = True
except ImportError:
    TASK_QUEUE_AVAILABLE = False
    list_pending_tasks = claim_task = complete_task = fail_task = lambda *a, **k: None

try:
    from config import get_ollama_client, OLLAMA_DEFAULT_MODEL, configure_ollama_env
    configure_ollama_env()
    ollama = get_ollama_client()
except Exception:
    ollama = None
    OLLAMA_DEFAULT_MODEL = "qwen2.5:32b"

logger = logging.getLogger("MemorySynthesizer")


class MemorySynthesizerAgent(BaseMCPAgent):
    """
    Sub-agent specialized in memory maintenance and synthesis.
    """

    def __init__(self, name: str = "memory_synthesizer"):
        super().__init__(name=name)
        try:
            from config import configure_ollama_env
            configure_ollama_env()
        except Exception:
            pass
        try:
            self.vm = VectorMemory()  # Shared persistent vector memory
        except Exception as e:
            logger.error(f"VectorMemory init failed: {e}")
            self.vm = None

        # Register custom handler
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "memory_synthesis",
            "consolidation",
            "deduplication",
            "importance_scoring",
            "memory_health_reporting",
            "reflection_generation"
        ]

    # -------------------------------------------------------------------------
    # Main Task Handler
    # -------------------------------------------------------------------------

    def handle_task_request(self, msg: MCPMessage):
        task_type = msg.payload.get("task_type", "full_synthesis")
        context = msg.payload.get("context", {})
        project = context.get("project", "general")

        logger.info(f"MemorySynthesizer received task: {task_type} | project={project}")

        result = {"status": "started", "task_type": task_type}

        if task_type in ["full_synthesis", "consolidate_all"]:
            result = self._run_full_synthesis(context)
        elif task_type == "project_synthesis":
            result = self._run_project_synthesis(project, context)
        elif task_type == "importance_scoring":
            result = self._run_importance_scoring(context)
        elif task_type == "generate_reflection":
            result = self._generate_periodic_reflection(context)
        elif task_type == "health_report":
            result = self._generate_memory_health_report(context)
        elif task_type in ["advanced_clustering", "cluster_and_synthesize"]:
            result = self._run_advanced_semantic_clustering(context)
        else:
            result = {"status": "error", "message": f"Unknown task_type: {task_type}"}

        # Report result back
        self.mcp.report_result(
            to_agent=msg.from_agent,
            correlation_id=msg.correlation_id,
            result=result
        )

        # Optionally store a high-level summary of what was done
        if result.get("status") == "success" and getattr(self, "vm", None) is not None:
            self.vm.add(
                content=f"MemorySynthesizer completed {task_type}. Summary: {result.get('summary', '')}",
                metadata={
                    "type": "synthesis_log",
                    "task_type": task_type,
                    "project": project,
                    "agent": self.name,
                    "timestamp": time.time()
                }
            )

    # -------------------------------------------------------------------------
    # Synthesis Logic
    # -------------------------------------------------------------------------

    def _run_full_synthesis(self, context: Dict) -> Dict:
        """Run a broad synthesis pass across all or filtered memories."""
        # For now, we do a simplified version. In a more advanced implementation
        # we would cluster embeddings, find duplicates, etc.

        all_memories = self.vm.get_all(limit=500)  # Reasonable batch
        if not all_memories.get("documents"):
            return {"status": "success", "summary": "No memories to synthesize yet."}

        documents = all_memories["documents"]
        metadatas = all_memories.get("metadatas", [])

        synthesized_count = 0
        archived_count = 0

        # Simple heuristic + LLM-assisted synthesis for important clusters
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            if not doc:
                continue

            # Example: Synthesize reflections older than X or very long ones
            if meta.get("type") in ["reflection", "research"] and len(doc) > 800:
                summary = self._llm_summarize(doc, meta)
                if summary and len(summary) < len(doc) * 0.6:
                    # Store synthesized version
                    self.vm.add(
                        content=summary,
                        metadata={
                            **meta,
                            "type": "synthesized",
                            "original_id": all_memories["ids"][i] if "ids" in all_memories else None,
                            "synthesized_by": self.name,
                            "timestamp": time.time()
                        }
                    )
                    synthesized_count += 1

                    # Optionally mark original for archival (soft delete in real impl)
                    archived_count += 1

        summary_text = f"Synthesized {synthesized_count} entries. Archived {archived_count} originals."
        return {
            "status": "success",
            "synthesized_count": synthesized_count,
            "archived_count": archived_count,
            "summary": summary_text
        }

    def _run_project_synthesis(self, project: str, context: Dict) -> Dict:
        """Focused synthesis for one project."""
        results = self.vm.query(
            query_text=f"important insights and decisions about {project}",
            n_results=30,
            filter={"project": project}
        )

        if not results.get("documents") or not results["documents"][0]:
            return {"status": "success", "summary": f"No memories found for project {project}"}

        # Combine top relevant memories and synthesize
        combined = "\n\n---\n\n".join(results["documents"][0][:15])
        synthesized = self._llm_summarize(
            combined,
            {"project": project, "type": "project_overview"}
        )

        if synthesized:
            self.vm.add(
                content=synthesized,
                metadata={
                    "type": "project_synthesis",
                    "project": project,
                    "agent": self.name,
                    "timestamp": time.time(),
                    "source_memories_count": len(results["documents"][0])
                }
            )

        return {
            "status": "success",
            "project": project,
            "synthesized_overview_length": len(synthesized) if synthesized else 0,
            "summary": f"Created project-level synthesis for {project}"
        }

    def _run_importance_scoring(self, context: Dict) -> Dict:
        """Score memories for importance and persist scores in metadata."""
        if self.vm is None:
            return {"status": "error", "message": "VectorMemory is not available"}
        scored = 0
        updated = 0
        memories = self.vm.get_all(limit=int(context.get("limit", 200)))
        docs = memories.get("documents", []) or []
        metas = memories.get("metadatas", []) or []
        ids = memories.get("ids", []) or []

        updated_metas = []
        updated_ids = []
        for i, doc in enumerate(docs):
            if not doc:
                continue
            meta = dict(metas[i] if i < len(metas) and metas[i] else {})
            score = self._llm_importance_score(doc, meta)
            meta["importance_score"] = round(score, 4)
            meta["importance_scored_at"] = time.time()
            scored += 1
            if i < len(ids):
                updated_ids.append(ids[i])
                updated_metas.append(meta)

        if updated_ids:
            self.vm.collection.update(ids=updated_ids, metadatas=updated_metas)
            updated = len(updated_ids)

        return {
            "status": "success",
            "scored_count": scored,
            "metadata_updated": updated,
            "summary": f"Scored importance for {scored} memory entries and updated {updated} metadata records."
        }

    def _generate_periodic_reflection(self, context: Dict) -> Dict:
        """Generate a high-level reflection from recent memories."""
        recent = self.vm.query(
            query_text="recent important events, decisions, and learnings",
            n_results=10
        )

        if not recent.get("documents"):
            return {"status": "success", "summary": "Not enough recent activity for reflection."}

        combined = "\n\n".join(recent["documents"][0])
        reflection = self._llm_generate_reflection(combined)

        if reflection:
            self.vm.add_reflection(
                content=reflection,
                project=context.get("project", "general"),
                tags=["periodic_reflection", "synthesized"]
            )

        return {
            "status": "success",
            "reflection_length": len(reflection) if reflection else 0,
            "summary": "Generated periodic synthesized reflection."
        }

    def _generate_memory_health_report(self, context: Dict) -> Dict:
        """Produce a report on the current state of vector memory."""
        count = self.vm.count()
        # In future versions: analyze distribution by type/project, age, redundancy, etc.

        report = f"""Memory Health Report ({time.strftime('%Y-%m-%d')}):
- Total entries: {count}
- Status: Healthy (basic metrics only in v0.1)
- Recommendations: Run full synthesis weekly. Implement importance-based retention policy.
"""
        self.vm.add(
            content=report,
            metadata={"type": "memory_health_report", "agent": self.name}
        )

        return {
            "status": "success",
            "total_entries": count,
            "report": report,
            "summary": "Generated memory health report."
        }

    def _run_advanced_semantic_clustering(self, context: Dict) -> Dict:
        """Use advanced semantic clustering + LLM synthesis."""
        try:
            from vector_memory.semantic_clustering import SemanticClustering
        except ImportError:
            return {
                "status": "error",
                "message": "semantic_clustering module not available. Install hdbscan + umap-learn."
            }

        clusterer = SemanticClustering(self.vm)

        n_results = context.get("n_results", 800)
        min_cluster_size = context.get("min_cluster_size", 4)

        logger.info(f"Running advanced semantic clustering (n_results={n_results})...")

        result = clusterer.cluster_and_synthesize(
            n_results=n_results,
            min_cluster_size=min_cluster_size,
            store_summaries=True
        )

        return {
            "status": "success",
            "clusters_found": result.get("clusters_found", 0),
            "summaries_stored": result.get("summaries_stored", 0),
            "duration_seconds": result.get("duration_seconds", 0),
            "summary": result.get("message", "Advanced semantic clustering completed.")
        }

    # -------------------------------------------------------------------------
    # LLM Helper Methods (via Ollama)
    # -------------------------------------------------------------------------

    def _llm_summarize(self, text: str, meta: Dict) -> Optional[str]:
        if not ollama:
            return None
        try:
            prompt = f"""You are an expert memory synthesizer for an autonomous AI agent.

Condense the following memory entry into a concise, high-signal summary while preserving key facts, decisions, and insights. 
Keep it under 60% of the original length if possible.

Metadata: {meta}

Content:
{text}

High-quality synthesized summary:"""

            response = ollama.chat(
                model=OLLAMA_DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "num_ctx": 16384}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return None

    def _llm_importance_score(self, text: str, meta: Dict) -> float:
        """Return deterministic importance score from content and metadata signals."""
        score = 0.35
        memory_type = str(meta.get("type", "")).lower()
        if memory_type in {"reflection", "decision", "project_synthesis"}:
            score += 0.35
        elif memory_type in {"research", "mcp_message", "memory_health_report"}:
            score += 0.15

        text_l = text.lower()
        high_signal_terms = [
            "decision", "root cause", "fix", "bug", "lesson", "rollback",
            "approval", "risk", "architecture", "test", "verified", "failed",
        ]
        score += min(0.2, 0.025 * sum(1 for term in high_signal_terms if term in text_l))

        if len(text) > 2000:
            score += 0.05
        if re.search(r"https?://|commit|trace_id|proposal", text_l):
            score += 0.05
        if len(text.strip()) < 40:
            score -= 0.2
        if meta.get("importance_score") is not None:
            score = max(score, float(meta.get("importance_score", 0)))
        return max(0.0, min(1.0, score))

    def _llm_generate_reflection(self, combined_memories: str) -> Optional[str]:
        if not ollama:
            return None
        try:
            prompt = f"""You are Hermes' MemorySynthesizer. Generate a thoughtful, concise periodic reflection 
based on the recent memories below. Focus on key learnings, patterns, wins, and areas for improvement.

Recent memories:
{combined_memories[:8000]}

Periodic Reflection:"""

            response = ollama.chat(
                model=OLLAMA_DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.4}
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Reflection generation failed: {e}")
            return None


    def run_loop(self, poll_interval: float = 3.0):
        """Override to also process the shared task queue."""
        logger.info(f"Starting MemorySynthesizer with shared task queue support")
        try:
            while True:
                # Process incoming MCP messages
                responses = self.mcp.process_inbox()
                for r in responses:
                    if r.to_agent != "broadcast":
                        self.mcp.transport.send(r)

                # Process tasks from shared file-based queue
                if TASK_QUEUE_AVAILABLE:
                    self._process_shared_task_queue()

                time.sleep(poll_interval)
        except KeyboardInterrupt:
            logger.info("MemorySynthesizer shutting down...")
            self.registry.deregister(self.name)

    def _process_shared_task_queue(self):
        """Check for and execute tasks created by the dashboard or other sources."""
        try:
            pending_tasks = list_pending_tasks()
            if not pending_tasks:
                return

            for task in pending_tasks[:2]:  # Limit per cycle
                task_id = task["id"]
                task_type = task.get("task_type")

                if not claim_task(task_id):
                    continue

                logger.info(f"Processing shared task: {task_type} ({task_id[:8]}...)")

                try:
                    if task_type in ["advanced_clustering", "cluster_and_synthesize"]:
                        result = self._run_advanced_semantic_clustering(task.get("payload", {}))
                    elif task_type == "full_synthesis":
                        result = self._run_full_synthesis(task.get("payload", {}))
                    elif task_type == "generate_reflection":
                        result = self._generate_periodic_reflection(task.get("payload", {}))
                    elif task_type == "health_report":
                        result = self._generate_memory_health_report(task.get("payload", {}))
                    else:
                        result = {"status": "unknown_task_type"}

                    complete_task(task_id, result)
                    logger.info(f"Completed shared task {task_id[:8]}")

                except Exception as e:
                    logger.exception(f"Task {task_id} failed")
                    fail_task(task_id, str(e))

        except Exception as e:
            logger.error(f"Error processing shared task queue: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Starting MemorySynthesizer Sub-Agent with Shared Task Queue...")
    agent = MemorySynthesizerAgent()
    agent.run_loop()