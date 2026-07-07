"""
Vector Memory Integration for Hermes
====================================

Provides persistent, semantic (vector) memory capabilities using:
- ChromaDB as the vector store (local, persistent, production-grade)
- Ollama embedding models (fully local, e.g. nomic-embed-text, mxbai-embed-large)

This enables Hermes and its sub-agents to:
- Store and retrieve knowledge semantically
- Maintain long-term project memory and research synthesis
- Share context across MCP sub-agents
- Perform reflective retrieval ("what did I learn about X before?")
- Accelerate self-improvement by recalling past decisions, failures, and insights

Location: memory/vector_db/ (persistent)
"""

from __future__ import annotations
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger("Hermes.VectorMemory")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed. Run: pip install chromadb")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("ollama Python client not installed. Run: pip install ollama")


@dataclass
class MemoryItem:
    """Standard item for vector memory storage."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    embedding: Optional[List[float]] = None


class VectorMemory:
    """
    High-level vector memory interface for Hermes.

    Usage:
        vm = VectorMemory()
        vm.add("Key insight about project X...", metadata={"project": "trading_bot", "agent": "hermes", "type": "reflection"})
        results = vm.query("How to improve the trading strategy?", n_results=5, filter={"project": "trading_bot"})
    """

    def __init__(
        self,
        persist_directory: str = "memory/vector_db",
        collection_name: str = "hermes_knowledge",
        embedding_model: str = "nomic-embed-text",   # Excellent local embedding model via Ollama
        ollama_host: str = "http://localhost:11434",
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.ollama_host = ollama_host

        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb is required for VectorMemory. Install with: pip install chromadb")

        # Initialize Chroma client (persistent)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}  # Good for semantic similarity
        )

        logger.info(f"VectorMemory initialized. Collection: {collection_name} | Embeddings: {embedding_model}")

    # -------------------------------------------------------------------------
    # Embedding
    # -------------------------------------------------------------------------

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama (preferred) or fallback."""
        if OLLAMA_AVAILABLE:
            try:
                response = ollama.embeddings(
                    model=self.embedding_model,
                    prompt=text,
                    options={"num_ctx": 8192}  # Good context for embeddings
                )
                return response["embedding"]
            except Exception as e:
                logger.error(f"Ollama embedding failed: {e}. Falling back to random (not recommended).")
                # In production you would raise or use a local sentence-transformers model
                import random
                return [random.random() for _ in range(768)]

        # Fallback (should be avoided in real use)
        import random
        logger.warning("Using random embeddings - install ollama + pull embedding model")
        return [random.random() for _ in range(768)]

    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------

    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
    ) -> str:
        """
        Add a memory item. Automatically generates embedding via Ollama.
        """
        if not content or not content.strip():
            return ""

        item_id = id or str(uuid.uuid4())
        meta = metadata or {}
        meta.setdefault("timestamp", time.time())
        meta.setdefault("source", "hermes")

        embedding = self._get_embedding(content)

        self.collection.add(
            ids=[item_id],
            documents=[content],
            metadatas=[meta],
            embeddings=[embedding]
        )

        logger.debug(f"Added memory item | id={item_id} | meta={meta}")
        return item_id

    def add_many(self, items: List[Dict[str, Any]]) -> List[str]:
        """Batch add multiple items."""
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for item in items:
            content = item["content"]
            meta = item.get("metadata", {})
            meta.setdefault("timestamp", time.time())
            meta.setdefault("source", "hermes")

            item_id = item.get("id", str(uuid.uuid4()))
            ids.append(item_id)
            documents.append(content)
            metadatas.append(meta)
            embeddings.append(self._get_embedding(content))

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        return ids

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include: List[str] = ["documents", "metadatas", "distances"]
    ) -> Dict[str, Any]:
        """
        Semantic search. Returns most relevant memories.
        """
        query_embedding = self._get_embedding(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter,
            include=include
        )
        return results

    def get_relevant_context(
        self,
        query: str,
        n_results: int = 6,
        filter: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4000
    ) -> str:
        """
        Returns a concatenated string of the most relevant memories,
        suitable for injecting into an LLM prompt.
        """
        results = self.query(query, n_results=n_results, filter=filter)

        if not results.get("documents") or not results["documents"][0]:
            return ""

        context_parts = []
        total_chars = 0

        for doc, meta, dist in zip(
            results["documents"][0],
            results.get("metadatas", [[]])[0],
            results.get("distances", [[]])[0]
        ):
            part = f"[Relevance: {1 - dist:.2f}] {doc}"
            if meta:
                part += f"\n  (source: {meta.get('source', 'unknown')}, project: {meta.get('project', 'general')})"

            if total_chars + len(part) > max_tokens * 4:  # rough char limit
                break
            context_parts.append(part)
            total_chars += len(part)

        return "\n\n---\n\n".join(context_parts)

    def delete(self, ids: List[str]):
        self.collection.delete(ids=ids)

    def count(self) -> int:
        return self.collection.count()

    def get_all(self, limit: int = 100) -> Dict:
        return self.collection.get(limit=limit)

    # -------------------------------------------------------------------------
    # Hermes-Specific Helpers
    # -------------------------------------------------------------------------

    def add_reflection(self, content: str, project: str = "general", tags: Optional[List[str]] = None):
        """Convenience method for storing reflections / self-improvement notes."""
        return self.add(
            content=content,
            metadata={
                "type": "reflection",
                "project": project,
                "tags": tags or [],
                "source": "hermes"
            }
        )

    def add_research_finding(self, content: str, project: str, source_url: Optional[str] = None):
        return self.add(
            content=content,
            metadata={
                "type": "research",
                "project": project,
                "source_url": source_url,
                "source": "hermes"
            }
        )

    def add_mcp_interaction(self, content: str, from_agent: str, to_agent: str, message_type: str):
        """Store important MCP messages for long-term semantic recall."""
        return self.add(
            content=content,
            metadata={
                "type": "mcp_message",
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message_type": message_type,
                "source": "mcp"
            }
        )


# =============================================================================
# Factory / Config Helper
# =============================================================================

def get_vector_memory(config: Optional[Dict] = None) -> VectorMemory:
    """Factory function. Reads from config.json if available."""
    config = config or {}
    return VectorMemory(
        persist_directory=config.get("vector_db_path", "memory/vector_db"),
        collection_name=config.get("vector_collection", "hermes_knowledge"),
        embedding_model=config.get("embedding_model", "nomic-embed-text"),
    )


if __name__ == "__main__":
    print("Vector Memory module loaded.")
    print("Recommended: pip install chromadb ollama")
    print("Then pull an embedding model: ollama pull nomic-embed-text")