"""Basic unit tests for tracing systems"""
import tempfile
from tracing.task_trace import TaskTracer
from tracing.proposal import ProposalStore, ImprovementProposal, ProposalType, RiskLevel

def test_trace_creation():
    with tempfile.TemporaryDirectory() as tmp:
        t = TaskTracer(log_dir=tmp)
        tid = t.start_trace("test", "tester", {"input": 1})
        assert tid is not None
        t.end_trace(tid, {"output": 2})
        assert len(t.get_recent_traces()) >= 1

def test_proposal_creation():
    with tempfile.TemporaryDirectory() as tmp:
        store = ProposalStore(storage_dir=tmp)
        p = ImprovementProposal(
            id="test-1",
            type=ProposalType.CODE_EDIT,
            title="Test",
            description="Test proposal",
            reason="Testing",
            risk_level=RiskLevel.LOW
        )
        path = store.save(p)
        assert path.exists()
        loaded = store.load("test-1")
        assert loaded is not None
        assert loaded.title == "Test"