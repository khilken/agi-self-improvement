"""Regression tests for proposal application and auto-apply safety."""


from tracing.apply import ProposalApplicator
from tracing.auto_apply import AutoApplyEngine
from tracing.proposal import ImprovementProposal, ProposalType, RiskLevel, ProposalStore


def test_full_file_apply_and_rollback(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("old\n")

    proposal = ImprovementProposal(
        id="apply-test",
        type=ProposalType.CODE_EDIT,
        title="Replace target",
        description="Replace file contents",
        reason="Regression test",
        target_file=str(target),
        diff="new\n",
        risk_level=RiskLevel.LOW,
    )

    app = ProposalApplicator(backup_dir=str(tmp_path / "backups"))
    ok, msg = app.apply(proposal)
    assert ok, msg
    assert target.read_text() == "new\n"

    backups = list((tmp_path / "backups").glob("*.bak"))
    assert backups
    assert app.rollback(proposal.id, str(backups[0]), target_path=str(target))
    assert target.read_text() == "old\n"


def test_auto_apply_verifies_and_records(tmp_path):
    proposal_dir = tmp_path / "proposals"
    approval_dir = tmp_path / "approvals"
    history_dir = tmp_path / "history"

    proposal = ImprovementProposal(
        id="low-risk-1",
        type=ProposalType.PROCESS_IMPROVEMENT,
        title="Improve process",
        description="Small safe process improvement",
        reason="Regression test",
        risk_level=RiskLevel.LOW,
    )
    ProposalStore(storage_dir=str(proposal_dir)).save(proposal)

    engine = AutoApplyEngine()
    engine.proposal_store = ProposalStore(storage_dir=str(proposal_dir))
    from tracing.approval import ApprovalGate
    from tracing.history import ImprovementHistory
    engine.approval_gate = ApprovalGate(storage_dir=str(approval_dir))
    engine.history = ImprovementHistory(storage_dir=str(history_dir))

    applied = engine.process_low_risk_proposals()
    assert applied == ["low-risk-1"]
    assert engine.approval_gate.get_status("low-risk-1").status.value == "approved"
    assert engine.history.get_history("low-risk-1")
