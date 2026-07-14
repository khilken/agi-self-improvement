#!/usr/bin/env python3
"""
Hermes Improvement Proposal Review CLI
======================================

Simple command-line tool to review and manage improvement proposals.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracing.proposal import ProposalStore
from tracing.approval import ApprovalGate
from tracing.history import ImprovementHistory


def main():
    proposal_store = ProposalStore()
    approval_gate = ApprovalGate()
    history = ImprovementHistory()

    print("=== Hermes Improvement Review CLI ===\n")

    # Show pending approvals
    pending = approval_gate.list_pending()
    print(f"Pending Approvals: {len(pending)}")

    if pending:
        for record in pending:
            proposal = proposal_store.load(record.proposal_id)
            if proposal:
                print(f"\n[{proposal.priority.upper()}] {proposal.title}")
                print(f"  ID: {proposal.id}")
                print(f"  Risk: {proposal.risk_level}")
                print(f"  Reason: {proposal.reason}")
                print(f"  Impact: {proposal.estimated_impact}")

    # Show recent history
    print("\n\nRecent Activity:")
    events = history.get_timeline(limit=10)
    for event in events:
        print(f"  [{event.timestamp[:19]}] {event.event_type.value} - {event.proposal_id[:8]}")

    print("\nUse the ApprovalGate API for approve/reject/modify actions.")


if __name__ == "__main__":
    main()