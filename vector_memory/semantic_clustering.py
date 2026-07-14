"""
Advanced Semantic Clustering for Hermes Vector Memory
=====================================================

This module provides production-grade semantic clustering on top of the
VectorMemory (ChromaDB) store.

Key Capabilities:
- Fetch embeddings + metadata from ChromaDB
- Dimensionality reduction with UMAP (highly recommended for semantic data)
- Density-based clustering with HDBSCAN (no need to predefine k)
- Cluster analysis and statistics
- Integration point for MemorySynthesizer to perform intelligent consolidation

This dramatically improves memory quality by:
- Discovering related but non-identical memories
- Enabling cluster-level summarization (higher abstraction)
- Supporting better deduplication and importance scoring
- Creating "topic maps" of Hermes' accumulated knowledge

Dependencies (recommended):
    pip install hdbscan umap-learn scikit-learn numpy
"""

from __future__ import annotations
import logging
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger("Hermes.SemanticClustering")

if TYPE_CHECKING:
    from vector_memory.vector_memory import VectorMemory

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    logger.warning("hdbscan not installed. Clustering quality will be reduced.")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logger.warning("umap-learn not installed. Using raw embeddings for clustering.")

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class SemanticCluster:
    """Represents one semantic cluster of memories."""
    cluster_id: int
    member_ids: List[str]
    member_documents: List[str]
    member_metadatas: List[Dict[str, Any]]
    centroid: Optional[np.ndarray] = None
    size: int = 0
    avg_relevance: float = 0.0
    summary: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class SemanticClustering:
    """
    Advanced semantic clustering engine for Hermes memory.

    Usage:
        from vector_memory import VectorMemory, SemanticClustering

        vm = VectorMemory()
        clusterer = SemanticClustering(vm)
        clusters = clusterer.cluster_memories(n_results=500, min_cluster_size=3)
        clusterer.summarize_clusters(clusters)  # LLM-powered
    """

    def __init__(self, vector_memory: "VectorMemory"):
        self.vm = vector_memory
        self.collection = vector_memory.collection

    # -------------------------------------------------------------------------
    # Core Clustering Pipeline
    # -------------------------------------------------------------------------

    def cluster_memories(
        self,
        n_results: int = 1000,
        min_cluster_size: int = 3,
        min_samples: int = 2,
        use_umap: bool = True,
        umap_n_components: int = 20,
        random_state: int = 42
    ) -> List[SemanticCluster]:
        """
        Perform advanced semantic clustering on recent/relevant memories.

        Returns a list of SemanticCluster objects.
        """
        logger.info(f"Starting semantic clustering on up to {n_results} memories...")

        # 1. Fetch data from ChromaDB
        data = cast(Dict[str, Any], self.collection.get(
            limit=n_results,
            include=["documents", "metadatas", "embeddings"]
        ))

        raw_embeddings = data.get("embeddings") or []
        if len(raw_embeddings) == 0:
            logger.warning("No embeddings found for clustering.")
            return []

        embeddings = np.array(raw_embeddings)
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = [dict(meta or {}) for meta in (data.get("metadatas", []) or [])]

        logger.info(f"Fetched {len(embeddings)} embeddings for clustering.")

        # 2. Optional: UMAP dimensionality reduction (strongly recommended)
        reduced_embeddings = embeddings
        if use_umap and UMAP_AVAILABLE and embeddings.shape[1] > umap_n_components:
            logger.info("Reducing dimensionality with UMAP...")
            reducer = umap.UMAP(
                n_components=umap_n_components,
                n_neighbors=15,
                min_dist=0.0,
                metric="cosine",
                random_state=random_state
            )
            reduced_embeddings = reducer.fit_transform(embeddings)
            logger.info(f"Reduced to {reduced_embeddings.shape[1]} dimensions.")

        # 3. Clustering
        if HDBSCAN_AVAILABLE:
            logger.info("Clustering with HDBSCAN...")
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min_cluster_size,
                min_samples=min_samples,
                metric="euclidean",
                cluster_selection_method="eom"
            )
            labels = clusterer.fit_predict(reduced_embeddings)
        elif SKLEARN_AVAILABLE:
            logger.info("HDBSCAN not available — falling back to KMeans.")
            n_clusters = max(5, len(embeddings) // 20)
            kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
            labels = kmeans.fit_predict(reduced_embeddings)
        else:
            logger.error("No clustering library available (hdbscan or scikit-learn).")
            return []

        # 4. Group into SemanticCluster objects
        clusters: Dict[int, SemanticCluster] = {}
        noise_label = -1

        for i, label in enumerate(labels):
            if label == noise_label:
                continue  # Skip noise points for now

            if label not in clusters:
                clusters[label] = SemanticCluster(
                    cluster_id=int(label),
                    member_ids=[],
                    member_documents=[],
                    member_metadatas=[],
                    size=0
                )

            clusters[label].member_ids.append(ids[i])
            clusters[label].member_documents.append(documents[i])
            clusters[label].member_metadatas.append(metadatas[i] if metadatas else {})
            clusters[label].size += 1

        # Calculate centroids (on reduced space)
        for cluster in clusters.values():
            if cluster.member_ids:
                member_indices = [ids.index(mid) for mid in cluster.member_ids if mid in ids]
                if member_indices:
                    cluster.centroid = np.mean(reduced_embeddings[member_indices], axis=0)

        result = list(clusters.values())
        logger.info(f"Found {len(result)} semantic clusters (plus noise).")
        return result

    # -------------------------------------------------------------------------
    # LLM-Powered Cluster Summarization
    # -------------------------------------------------------------------------

    def summarize_clusters(
        self,
        clusters: List[SemanticCluster],
        llm_model: str = "qwen2.5:32b"
    ) -> List[SemanticCluster]:
        """
        Generate high-quality summaries for each cluster using the LLM.
        Also extracts emergent tags/themes.
        """
        try:
            import ollama
        except ImportError:
            logger.warning("ollama not available for cluster summarization.")
            return clusters

        for cluster in clusters:
            if not cluster.member_documents:
                continue

            # Create a combined text for the cluster (limit length)
            combined_text = "\n\n---\n\n".join(cluster.member_documents[:8])  # top 8 members
            if len(combined_text) > 12000:
                combined_text = combined_text[:12000]

            prompt = f"""You are an expert memory synthesizer for an autonomous AI system called Hermes.

Analyze the following group of related memories (a semantic cluster). 
Provide:
1. A concise, high-signal summary of the core theme / insight of this cluster (2-4 sentences).
2. 3-6 emergent tags or topics that describe this cluster.

Cluster size: {cluster.size}
Sample memories:
{combined_text}

Respond in this exact format:
SUMMARY: <your summary here>
TAGS: tag1, tag2, tag3, ..."""

            try:
                response = ollama.chat(
                    model=llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.3, "num_ctx": 16384}
                )
                content = response["message"]["content"]

                # Parse response
                if "SUMMARY:" in content:
                    summary_part = content.split("SUMMARY:")[1]
                    if "TAGS:" in summary_part:
                        summary, tags_part = summary_part.split("TAGS:", 1)
                        cluster.summary = summary.strip()
                        cluster.tags = [t.strip() for t in tags_part.strip().split(",") if t.strip()]
                    else:
                        cluster.summary = summary_part.strip()
                else:
                    cluster.summary = content.strip()[:500]

                logger.info(f"Cluster {cluster.cluster_id} summarized. Tags: {cluster.tags}")

            except Exception as e:
                logger.error(f"Failed to summarize cluster {cluster.cluster_id}: {e}")
                cluster.summary = " (LLM summarization failed)"

        return clusters

    # -------------------------------------------------------------------------
    # High-Level Workflow: Cluster → Synthesize → Store
    # -------------------------------------------------------------------------

    def cluster_and_synthesize(
        self,
        n_results: int = 800,
        min_cluster_size: int = 4,
        store_summaries: bool = True,
        llm_model: str = "qwen2.5:32b"
    ) -> Dict[str, Any]:
        """
        End-to-end advanced clustering + synthesis workflow.
        This is the main method the MemorySynthesizer should call.
        """
        start_time = time.time()

        # Step 1: Cluster
        clusters = self.cluster_memories(
            n_results=n_results,
            min_cluster_size=min_cluster_size
        )

        if not clusters:
            return {"status": "success", "message": "No clusters found.", "clusters": 0}

        # Step 2: Summarize clusters with LLM
        clusters = self.summarize_clusters(clusters, llm_model=llm_model)

        synthesized_count = 0

        # Step 3: Store high-quality cluster summaries back into Vector Memory
        if store_summaries:
            for cluster in clusters:
                if cluster.summary and len(cluster.summary) > 30:
                    self.vm.add(
                        content=cluster.summary,
                        metadata={
                            "type": "cluster_synthesis",
                            "cluster_id": cluster.cluster_id,
                            "cluster_size": cluster.size,
                            "tags": cluster.tags,
                            "member_ids": cluster.member_ids[:10],  # store sample
                            "synthesized_by": "semantic_clustering",
                            "timestamp": time.time()
                        }
                    )
                    synthesized_count += 1

        duration = time.time() - start_time

        return {
            "status": "success",
            "clusters_found": len(clusters),
            "summaries_stored": synthesized_count,
            "duration_seconds": round(duration, 2),
            "message": f"Advanced semantic clustering complete. Found {len(clusters)} clusters."
        }


# Convenience function
def get_semantic_clustering(vector_memory: Optional["VectorMemory"] = None) -> SemanticClustering:
    from vector_memory import VectorMemory as VM
    vm = vector_memory or VM()
    return SemanticClustering(vm)