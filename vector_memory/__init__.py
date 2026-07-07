"""
Hermes Vector Memory Package
============================

Persistent semantic memory using ChromaDB + Ollama embeddings.

Core class: VectorMemory
Factory: get_vector_memory(config)

Integrates deeply with:
- Hermes main loop (long-term knowledge, reflections, research)
- MCP protocol (sub-agents can contribute to and query shared memory)
"""

from .vector_memory import (
    VectorMemory,
    MemoryItem,
    get_vector_memory,
)
from .semantic_clustering import (
    SemanticClustering,
    SemanticCluster,
    get_semantic_clustering,
)

__version__ = "0.2.0"
__all__ = [
    "VectorMemory",
    "MemoryItem",
    "get_vector_memory",
    "SemanticClustering",
    "SemanticCluster",
    "get_semantic_clustering",
]