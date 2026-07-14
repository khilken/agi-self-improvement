#!/usr/bin/env python3
"""
Daily Self-Improvement Cron Job for Hermes
==========================================

Runs the full self-improvement loop with multi-level agents.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
import logging

from agents.meta_improver_agent import MetaImproverAgent
from agents.hyper_meta_improver_agent import HyperMetaImproverAgent
from agents.knowledge_curator_agent import KnowledgeCuratorAgent
from agents.safety_governance_agent import SafetyGovernanceAgent
from agents.long_horizon_planner_agent import LongHorizonPlannerAgent
from agents.experimentation_agent import ExperimentationAgent
from agents.self_verification_agent import SelfVerificationAgent
from agents.version_control_rollback_agent import VersionControlRollbackAgent
from tracing.auto_apply import AutoApplyEngine
from tracing.approval import ApprovalGate
from tracing.history import ImprovementHistory, HistoryEvent, HistoryEventType
from tracing.experiment import ExperimentStore
from mcp.protocol import MessageType, MCPMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DailySelfImprovement")


def _run_agent_task(agent, task_type: str, context: dict | None = None) -> dict:
    """Invoke agent handler with a synthetic TASK_REQUEST message."""
    context = context or {}
    msg = MCPMessage(
        from_agent="daily_self_improvement",
        to_agent=getattr(agent, "name", agent.__class__.__name__),
        message_type=MessageType.TASK_REQUEST,
        payload={"task_type": task_type, "context": context},
    )
    try:
        agent.handle_task_request(msg)
        return {"status": "ok", "agent": agent.__class__.__name__, "task_type": task_type}
    except Exception as e:
        logger.exception("%s failed", agent.__class__.__name__)
        return {"status": "error", "agent": agent.__class__.__name__, "error": str(e)}


def run_daily_self_improvement():
    print(f"\n{'='*60}")
    print(f"Daily Self-Improvement Run — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 1. Meta-Improver
    print("[1/8] Running Meta-Improver analysis...")
    improver = MetaImproverAgent()
    result = improver._analyze_and_generate_proposals()
    print(f"      Generated {result.get('proposals_generated', 0)} proposals (status={result.get('status')})")

    # 2. Hyper-Meta-Improver
    print("[2/8] Running Hyper-Meta-Improver...")
    hyper_improver = HyperMetaImproverAgent()
    hyper_result = hyper_improver._analyze_own_performance()
    print(f"      Generated {hyper_result.get('proposals_generated', 0)} meta-proposals")

    # 3. Knowledge + Safety + Planner
    print("[3/8] Knowledge Curator / Safety / Planner...")
    for agent_cls, ttype, ctx in [
        (KnowledgeCuratorAgent, "ingest", {"action": "ingest", "data": {"content": f"Daily run notes {datetime.now().isoformat()}"}}),
        (SafetyGovernanceAgent, "review", {"proposal": result}),
        (LongHorizonPlannerAgent, "plan", {"goal": "Continue recursive self-improvement of Hermes"}),
    ]:
        r = _run_agent_task(agent_cls(), ttype, ctx)
        print(f"      {r}")

    # 4. Experiment / Verify / Rollback agents (handlers)
    print("[4/8] Experimentation / Verification / Rollback...")
    for agent_cls, ttype in [
        (ExperimentationAgent, "design_experiment"),
        (SelfVerificationAgent, "verify"),
        (VersionControlRollbackAgent, "status"),
    ]:
        r = _run_agent_task(agent_cls(), ttype, {})
        print(f"      {r}")

    # 5. Auto-apply low-risk
    print("[5/8] Applying low-risk proposals...")
    auto_apply = AutoApplyEngine()
    applied = auto_apply.process_low_risk_proposals()
    print(f"      Auto-applied {len(applied)} proposals")

    # 6. Pending approvals
    print("[6/8] Checking pending approvals...")
    approval_gate = ApprovalGate()
    pending = approval_gate.list_pending()
    print(f"      {len(pending)} proposals waiting for human review")

    # 7. Experiment store record
    print("[7/8] Recording experiment + history...")
    try:
        store = ExperimentStore()
        exp = store.create(
            name="daily_self_improvement",
            variant_a={"strategy": "meta_only"},
            variant_b={"strategy": "meta_plus_hyper"},
        )
        store.record_result(
            exp.id,
            winner="variant_b",
            confidence=0.5,
            notes=f"proposals={result.get('proposals_generated', 0)} applied={len(applied)}",
        )
        print(f"      Experiment saved: {exp.id[:8]}")
    except Exception as e:
        print(f"      Experiment store skipped: {e}")

    history = ImprovementHistory()
    history.record(HistoryEvent(
        event_type=HistoryEventType.PROPOSAL_CREATED,
        proposal_id="daily_run",
        actor="daily_self_improvement",
        details={
            "proposals_generated": result.get("proposals_generated", 0),
            "hyper_proposals": hyper_result.get("proposals_generated", 0),
            "auto_applied": len(applied),
            "pending_review": len(pending),
        },
    ))

    # 8. Summary
    print("[8/8] Run complete.")
    print("\nSummary:")
    print(f"  - Proposals generated: {result.get('proposals_generated', 0)}")
    print(f"  - Hyper meta proposals: {hyper_result.get('proposals_generated', 0)}")
    print(f"  - Auto-applied (low risk): {len(applied)}")
    print(f"  - Pending human review: {len(pending)}")
    print(f"\n{'='*60}\n")
    return {
        "proposals": result.get("proposals_generated", 0),
        "hyper": hyper_result.get("proposals_generated", 0),
        "applied": len(applied),
        "pending": len(pending),
    }


if __name__ == "__main__":
    run_daily_self_improvement()
