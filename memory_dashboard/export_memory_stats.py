#!/usr/bin/env python3
"""
Memory Health Dashboard - Data Exporter
=======================================

This script queries the current state of Hermes Vector Memory + Semantic Clustering
and exports a rich JSON file that powers the Memory Health Dashboard.

Run this periodically (manually, via cron, or triggered by MemorySynthesizer/Hermes)
to keep the dashboard up to date.

Output: memory_health.json (consumed by memory_health_dashboard.html)
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    from vector_memory import VectorMemory, get_semantic_clustering
except ImportError:
    print("Error: vector_memory package not found. Run from the Hermes root directory.")
    exit(1)


def export_memory_health(output_path: str = "memory_dashboard/memory_health.json"):
    print("Exporting Hermes Memory Health data...")

    vm = VectorMemory()
    clusterer = get_semantic_clustering(vm)

    # Basic stats
    total_entries = vm.count()

    # Get recent data for analysis
    recent_data = vm.collection.get(
        limit=2000,
        include=["metadatas", "documents"]
    )

    metadatas = recent_data.get("metadatas", []) or []
    documents = recent_data.get("documents", []) or []

    # Distribution by type
    type_counts: Dict[str, int] = {}
    project_counts: Dict[str, int] = {}
    tag_counts: Dict[str, int] = {}

    for meta in metadatas:
        if not meta:
            continue
        t = str(meta.get("type", "unknown"))
        type_counts[t] = type_counts.get(t, 0) + 1

        proj = str(meta.get("project", "general"))
        project_counts[proj] = project_counts.get(proj, 0) + 1

        raw_tags = meta.get("tags", [])
        if isinstance(raw_tags, str):
            tags = [raw_tags]
        elif isinstance(raw_tags, list):
            tags = [str(tag) for tag in raw_tags]
        else:
            tags = []
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Recent syntheses (last 10)
    recent_syntheses = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        if meta and meta.get("type") in ["synthesized", "cluster_synthesis", "project_synthesis", "reflection"]:
            recent_syntheses.append({
                "content": doc[:300] + "..." if len(doc) > 300 else doc,
                "type": meta.get("type"),
                "project": meta.get("project", "general"),
                "timestamp": meta.get("timestamp", 0),
                "tags": meta.get("tags", [])
            })
            if len(recent_syntheses) >= 10:
                break

    # Run quick clustering stats (without full LLM summarization for speed)
    cluster_stats: Dict[str, Any]
    try:
        clusters = clusterer.cluster_memories(n_results=600, min_cluster_size=3)
        cluster_stats = {
            "total_clusters": len(clusters),
            "avg_cluster_size": round(sum(c.size for c in clusters) / len(clusters), 1) if clusters else 0,
            "largest_cluster": max((c.size for c in clusters), default=0),
            "clusters_with_summary": sum(1 for c in clusters if c.summary),
        }
    except Exception as e:
        print(f"Clustering stats failed: {e}")
        cluster_stats = {"total_clusters": 0, "error": str(e)}

    # Last synthesis info (from logs)
    last_synthesis = None
    for meta in metadatas:
        if meta and meta.get("type") == "synthesis_log":
            last_synthesis = {
                "task_type": meta.get("task_type"),
                "timestamp": meta.get("timestamp"),
                "project": meta.get("project")
            }
            break

    growth_trend = _calculate_growth_trend(total_entries, output_path)

    health_data = {
        "generated_at": datetime.now().isoformat(),
        "generated_at_unix": time.time(),
        "total_entries": total_entries,
        "type_distribution": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        "project_distribution": dict(sorted(project_counts.items(), key=lambda x: -x[1])),
        "top_tags": dict(sorted(tag_counts.items(), key=lambda x: -x[1])[:15]),
        "cluster_stats": cluster_stats,
        "recent_syntheses": recent_syntheses,
        "last_synthesis_run": last_synthesis,
        "memory_growth_trend": growth_trend,
        "health_score": _calculate_health_score(total_entries, cluster_stats, type_counts),
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(health_data, indent=2, default=str))

    print(f"Memory health data exported to: {output_file}")
    print(f"Total entries: {total_entries}")
    print(f"Clusters found: {cluster_stats.get('total_clusters', 0)}")
    return health_data


def _calculate_growth_trend(total_entries: int, output_path: str) -> str:
    """Compare current count with the previous dashboard export."""
    path = Path(output_path)
    if not path.exists():
        return "unknown"
    try:
        previous = json.loads(path.read_text())
        previous_total = int(previous.get("total_entries", total_entries))
    except Exception:
        return "unknown"
    delta = total_entries - previous_total
    if delta > 10:
        return "growing_fast"
    if delta > 0:
        return "growing"
    if delta < -10:
        return "shrinking_fast"
    if delta < 0:
        return "shrinking"
    return "stable"


def _calculate_health_score(total: int, cluster_stats: Dict, type_counts: Dict) -> float:
    """Simple heuristic health score (0-100). Can be improved later."""
    score = 50.0

    # More entries = better (up to a point)
    if total > 100:
        score += min(20, (total - 100) / 50)

    # Good clustering is healthy
    if cluster_stats.get("total_clusters", 0) > 5:
        score += 15

    # Having synthesized entries is very healthy
    if type_counts.get("synthesized", 0) > 5 or type_counts.get("cluster_synthesis", 0) > 0:
        score += 15

    return min(100.0, round(score, 1))


if __name__ == "__main__":
    export_memory_health()