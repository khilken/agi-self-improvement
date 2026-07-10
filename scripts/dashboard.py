#!/usr/bin/env python3
"""
Simple Observability Dashboard for Hermes
=========================================

Generates a basic HTML dashboard showing:
- Recent traces
- Improvement proposals
- Approval status
- System activity
"""

from pathlib import Path
import json
from datetime import datetime

# Import our systems
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracing.task_trace import tracer
from tracing.proposal import ProposalStore
from tracing.approval import ApprovalGate
from tracing.history import ImprovementHistory


def generate_dashboard(output_file: str = "logs/dashboard.html"):
    proposal_store = ProposalStore()
    approval_gate = ApprovalGate()
    history = ImprovementHistory()

    traces = tracer.get_recent_traces(limit=20)
    proposals = proposal_store.list_all()[:10]
    pending_approvals = approval_gate.list_pending()
    recent_events = history.get_timeline(limit=15)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Hermes Observability Dashboard</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; }}
        .section {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #3498db; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f1f3f5; }}
        .status-low {{ color: #27ae60; }}
        .status-medium {{ color: #f39c12; }}
        .status-high {{ color: #e74c3c; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Hermes Self-Improvement Dashboard</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="section">
        <h2>Overview</h2>
        <div class="metric">
            <div class="metric-value">{len(traces)}</div>
            <div>Recent Traces</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(proposals)}</div>
            <div>Proposals</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(pending_approvals)}</div>
            <div>Pending Approvals</div>
        </div>
    </div>

    <div class="section">
        <h2>Recent Improvement Proposals</h2>
        <table>
            <tr><th>Title</th><th>Type</th><th>Risk</th><th>Priority</th><th>Created</th></tr>
"""

    for p in proposals:
        risk_class = f"status-{p.risk_level.value}"
        html += f"<tr><td>{p.title}</td><td>{p.type.value}</td><td class='{risk_class}'>{p.risk_level.value}</td><td>{p.priority}</td><td>{p.created_at[:16]}</td></tr>"

    html += """
        </table>
    </div>

    <div class="section">
        <h2>Recent Activity</h2>
        <ul>
"""

    for event in recent_events:
        html += f"<li>[{event.timestamp[:16]}] {event.event_type.value} — {event.proposal_id[:8]}</li>"

    html += """
        </ul>
    </div>
</div>
</body>
</html>
"""

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(html)

    print(f"Dashboard generated: {output_file}")


if __name__ == "__main__":
    generate_dashboard()