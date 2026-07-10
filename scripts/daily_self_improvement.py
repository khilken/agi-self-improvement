#!/usr/bin/env python3
"""
Daily Self-Improvement Cron Job for Hermes
==========================================

Runs the full self-improvement loop:
- Analyzes traces
- Generates proposals
- Auto-applies low-risk improvements
- Submits higher-risk proposals for review
- Logs everything

Intended to be run daily via Hermes cron.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracing.task_trace import tracer
from agents.meta_improver_agent import MetaImproverAgent
from agents.hyper_meta_improver_agent import HyperMetaImproverAgent
from tracing.auto_apply import AutoApplyEngine
from tracing.approval import ApprovalGate
from tracing.history import ImprovementHistory, HistoryEvent, HistoryEventType
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DailySelfImprovement")


def run_daily_self_improvement():
    print(f"\n{'='*60}")
    print(f"Daily Self-Improvement Run — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # 1. Run Meta-Improver
    print("[1/5] Running Meta-Improver analysis...")
    improver = MetaImproverAgent()
    result = improver._analyze_and_generate_proposals()
    print(f"      Generated {result.get('proposals_generated', 0)} proposals")

    # 2. Run Hyper-Meta-Improver (improve the improver)
    print("[2/6] Running Hyper-Meta-Improver (metacognitive level)...")
    hyper_improver = HyperMetaImproverAgent()
    hyper_result = hyper_improver._analyze_own_performance()
    print(f"      Generated {hyper_result.get(proposals_generated, 0)} meta-proposals")

    # 3. Auto-apply low-risk proposals
    print("[3/6] Applying low-risk proposals...")
    auto_apply = AutoApplyEngine()
    applied = auto_apply.process_low_risk_proposals()
    print(f"      Auto-applied {len(applied)} proposals")

    # 3. Check pending approvals
    print("[4/6] Checking pending approvals...")
    approval_gate = ApprovalGate()
    pending = approval_gate.list_pending()
    print(f"      {len(pending)} proposals waiting for human review")

    # 4. Log the run
    print("[5/6] Recording history...")
    history = ImprovementHistory()
    history.record(HistoryEvent(
        event_type=HistoryEventType.PROPOSAL_CREATED,
        proposal_id="daily_run",
        actor="daily_self_improvement",
        details={
            "proposals_generated": result.get('proposals_generated', 0),
            "auto_applied": len(applied),
            "pending_review": len(pending)
        }
    ))

    # 5. Summary
    print("[6/6] Run complete.")
    print(f"\nSummary:")
    print(f"  - Proposals generated: {result.get('proposals_generated', 0)}")
    print(f"  - Auto-applied (low risk): {len(applied)}")
    print(f"  - Pending human review: {len(pending)}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run_daily_self_improvement()