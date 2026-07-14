#!/usr/bin/env python3
"""
Hermes Web Dashboard (Improved)
===============================

Interactive dashboard for reviewing proposals, approvals, and system status.
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from flask import Flask, render_template_string, request, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

    class _DummyFlask:
        def route(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

        def run(self, *args, **kwargs):
            raise RuntimeError("Flask is not installed. Install dependencies with: pip install -r requirements.txt")

    def Flask(name):  # type: ignore
        return _DummyFlask()

    def render_template_string(*args, **kwargs):  # type: ignore
        return "Flask is not installed"

    request = None  # type: ignore

    def redirect(target):  # type: ignore
        return target

    def url_for(name):  # type: ignore
        return name

from tracing.proposal import ProposalStore
from tracing.approval import ApprovalGate

app = Flask(__name__)

proposal_store = ProposalStore()
approval_gate = ApprovalGate()


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Hermes Dashboard</title>
    <style>
        body { font-family: system-ui; margin: 40px; background: #f8f9fa; }
        .container { max-width: 1100px; margin: 0 auto; }
        .proposal { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .risk-low { color: #27ae60; font-weight: bold; }
        .risk-medium { color: #f39c12; font-weight: bold; }
        .risk-high { color: #e74c3c; font-weight: bold; }
        button { padding: 8px 16px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .approve { background: #27ae60; color: white; }
        .reject { background: #e74c3c; color: white; }
    </style>
</head>
<body>
<div class="container">
    <h1>Hermes Improvement Dashboard</h1>
    <p><a href="/proposals">View All Proposals</a> | <a href="/pending">Pending Approvals</a></p>
    
    <h2>Pending Approvals</h2>
    {% for record in pending %}
        {% set p = proposals.get(record.proposal_id) %}
        {% if p %}
        <div class="proposal">
            <h3>{{ p.title }}</h3>
            <p><strong>Risk:</strong> <span class="risk-{{ p.risk_level.value }}">{{ p.risk_level.value }}</span></p>
            <p>{{ p.reason }}</p>
            <form method="post" action="/action">
                <input type="hidden" name="proposal_id" value="{{ p.id }}">
                <button type="submit" name="action" value="approve" class="approve">Approve</button>
                <button type="submit" name="action" value="reject" class="reject">Reject</button>
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
    return render_template_string(HTML, pending=pending, proposals=proposals)


@app.route("/action", methods=["POST"])
def action():
    pid = request.form.get("proposal_id")
    action = request.form.get("action")
    if action == "approve":
        approval_gate.approve(pid, reviewer="web")
    elif action == "reject":
        approval_gate.reject(pid, reviewer="web")
    return redirect(url_for("dashboard"))


@app.route("/proposals")
def all_proposals():
    props = proposal_store.list_all()
    return "<br>".join([f"{p.id[:8]} - {p.title} [{p.risk_level.value}]" for p in props])


if __name__ == "__main__":
    print("Hermes Dashboard running on http://localhost:8766")
    app.run(host="0.0.0.0", port=8766, debug=True)