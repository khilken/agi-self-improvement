# Vector Memory for Hermes

**Version:** 0.1.0  
**Status:** Integrated into Hermes v1.2+

## Purpose

Gives Hermes (and all its MCP sub-agents) **persistent semantic memory**. This is a critical capability for a self-sustaining AGI because it allows:

- Long-term retention of research, decisions, reflections, and lessons learned
- Semantic retrieval ("What did I previously conclude about X?")
- Cross-agent knowledge sharing via MCP
- Faster and higher-quality self-improvement cycles
- Context-aware reasoning without stuffing everything into the LLM context window

## Technology Stack (Local-First)

- **ChromaDB** — Persistent vector database (runs locally, no cloud)
- **Ollama** — Embedding generation (`nomic-embed-text` recommended — excellent quality and speed)
- Fully offline after models are pulled

## Quick Start

```bash
pip install chromadb ollama
ollama pull nomic-embed-text
```

```python
from vector_memory import VectorMemory

vm = VectorMemory()

# Store knowledge
vm.add(
    "The ORB strategy on penny stocks showed 72% win rate when volume filter > 1.5x average.",
    metadata={"project": "penny_stock_orb", "type": "research_finding", "agent": "hermes"}
)

# Semantic retrieval
context = vm.get_relevant_context(
    "How should I filter penny stock trades for higher win rate?",
    n_results=5,
    filter={"project": "penny_stock_orb"}
)

print(context)
```

## Integration with Hermes & MCP

Hermes now treats vector memory as a **core system capability** (see updated System Prompt v1.2).

Recommended usage patterns:

1. **After every significant reflection or research task** → `vm.add_reflection(...)` or `vm.add_research_finding(...)`
2. **Important MCP messages** → Store key interactions with `vm.add_mcp_interaction(...)`
3. **Before starting complex work** → Retrieve relevant context with `vm.get_relevant_context(...)` and inject into prompts
4. **Sub-agents** (via MCP) → Can be given access to query and contribute to the shared vector memory

## Recommended Metadata Schema

```python
metadata = {
    "type": "reflection" | "research" | "decision" | "mcp_message" | "code_change" | "error",
    "project": "project_name" or "general" or "self_improvement",
    "agent": "hermes" or "researcher" or "coder" etc.,
    "tags": ["tag1", "tag2"],
    "source": "hermes" | "mcp" | "web" | "user",
    "timestamp": float,
    "correlation_id": "..."   # link to MCP task chains
}
```

## Directory Structure

```
memory/
└── vector_db/          # ChromaDB persistent storage (do not edit manually)
    └── chroma.sqlite3
    └── ...

vector_memory/
├── __init__.py
├── vector_memory.py
└── README.md
```

## Self-Improvement Opportunities (for Hermes)

Hermes should actively work on improving this layer:

- Better chunking strategies for long documents
- Hybrid search (vector + keyword / metadata)
- Memory consolidation / summarization jobs
- Automatic forgetting / importance scoring
- Multi-collection architecture (one per major project + global)
- Integration with Obsidian (bidirectional sync of high-value notes)
- Evaluation of retrieval quality

## Advanced Semantic Clustering (New in v0.2)

Located in `semantic_clustering.py`.

Features:
- HDBSCAN density-based clustering (no need to specify number of clusters)
- UMAP dimensionality reduction for better semantic separation
- LLM-powered cluster summarization and emergent tag extraction
- End-to-end `cluster_and_synthesize()` workflow used by MemorySynthesizer

**Recommended dependencies:**
```bash
pip install hdbscan umap-learn scikit-learn
```

This enables true **knowledge crystallization** — turning many related memories into compact, high-signal cluster summaries.

## Future Enhancements (Hermes will implement)

- RAG pipelines with re-ranking
- Hierarchical memory (short-term working memory + long-term vector)
- Agent-specific memory views with permissioning
- Automated memory maintenance cron / background process
- Cross-cluster relationship mapping and knowledge graph construction

---

*Vector memory + Advanced Semantic Clustering is one of the most important upgrades on the path to self-sustaining AGI. It turns transient LLM context into durable, structured, queryable knowledge.*