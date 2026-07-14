"""Tests for remaining concrete fixes from the operational audit."""


from agents.memory_synthesizer import MemorySynthesizerAgent
from memory_dashboard.export_memory_stats import _calculate_growth_trend
from vector_memory.vector_memory import VectorMemory


def test_vector_memory_deterministic_embedding_fallback():
    vm = object.__new__(VectorMemory)
    a = vm._deterministic_embedding("same text")
    b = vm._deterministic_embedding("same text")
    c = vm._deterministic_embedding("different text")
    assert a == b
    assert a != c
    assert len(a) == 768
    assert abs(sum(x * x for x in a) - 1.0) < 1e-9


def test_memory_synthesizer_importance_score_uses_signals():
    agent = object.__new__(MemorySynthesizerAgent)
    low = agent._llm_importance_score("short", {})
    high = agent._llm_importance_score(
        "Decision: root cause fix verified with rollback test and proposal trace_id",
        {"type": "decision"},
    )
    assert high > low
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0


def test_memory_dashboard_growth_trend(tmp_path):
    output = tmp_path / "memory_health.json"
    assert _calculate_growth_trend(10, str(output)) == "unknown"
    output.write_text('{"total_entries": 10}')
    assert _calculate_growth_trend(10, str(output)) == "stable"
    assert _calculate_growth_trend(12, str(output)) == "growing"
    assert _calculate_growth_trend(30, str(output)) == "growing_fast"
    assert _calculate_growth_trend(8, str(output)) == "shrinking"
    assert _calculate_growth_trend(0, str(output)) == "shrinking"
