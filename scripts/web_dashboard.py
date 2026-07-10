#!/usr/bin/env python3
"""
Hermes Web Dashboard (Flask)
============================

Interactive web interface for reviewing and managing improvement proposals.
"""

from flask import Flask, render_template_string, request, redirect, url_for
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tracing.proposal import ProposalStore
from tracing.approval import ApprovalGate, ApprovalStatus

app = Flask(__name__)

proposal_store = ProposalStore()
approval_gate = ApprovalGate()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Hermes Proposal Review</title>
    <style>
        body { font-family: system-ui; margin: 40px; background: #f8f9fa; }
        .container { max-width: 1100px; margin: 0 auto; }
        .proposal { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .risk-low { color: #27ae60; }
        .risk-medium { color: #f39c12; }
        .risk-high { color: #e74c3c; }
        button { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .approve { background: #27ae60; color: white; }
        .reject { background: #e74c3c; color: white; }
        .modify { background: #3498db; color: white; }
    </style>
</head>
<body>
<div class="container">
    <h1>Hermes Improvement Proposals</h1>
    
    <h2>Pending Review</h2>
    {% for record in pending %}
        {% set proposal = proposals.get(record.proposal_id) %}
        {% if proposal %}
        <div class="proposal">
            <h3>{{ proposal.title }}</h3>
            <p><strong>Risk:</strong> <span class="risk-{{ proposal.risk_level.value }}">{{ proposal.risk_level.value }}</span></p>
            <p><strong>Reason:</strong> {{ proposal.reason }}</p>
            <p><strong>Impact:</strong> {{ proposal.estimated_impact }}</p>
            
            <form method="post" action="/action">
                <input type="hidden" name="proposal_id" value="{{ proposal.id }}">
                <button type="submit" name="action" value="approve" class="approve">Approve</button>
                <button type="submit" name="action" value="reject" class="reject">Reject</button>
                <button type="submit" name="action" value="modify" class="modify">Modify</button>
            </form>
        </div>
        {% endif %}
    {% endfor %}
</div>
</body>
</html>
"""


@app.route("/")
def dashboard():
    pending = approval_gate.list_pending()
    proposals = {p.id: p for p in proposal_store.list_all()}
    return render_template_string(HTML_TEMPLATE, pending=pending, proposals=proposals)

@app.route("/proposals")
def all_proposals():
    all_props = proposal_store.list_all()
    return "<br>".join([f"{p.id[:8]} - {p.title} [{p.risk_level}]" for p in all_props])


@app.route("/action", methods=["POST"])
def action():
    proposal_id = request.form.get("proposal_id")
    action = request.form.get("action")

    if action == "approve":
        approval_gate.approve(proposal_id, reviewer="web_dashboard")
    elif action == "reject":
        approval_gate.reject(proposal_id, reviewer="web_dashboard")
    elif action == "modify":
        # For simplicity, just approve with note
        approval_gate.modify(proposal_id, reviewer="web_dashboard", modified_diff="User modified", notes="Modified via web")

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    print("Starting Hermes Web Dashboard on http://localhost:8766")
    app.run(host="0.0.0.0", port=8766, debug=True)