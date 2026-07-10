#!/usr/bin/env python3
"""
Daily Summary Email Cron Job
============================

Generates a summary of the day's self-improvement and research activities
and emails it to khilken1@gmail.com.
"""

import sys
from pathlib import Path
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from tracing.history import ImprovementHistory
from tracing.proposal import ProposalStore
from tracing.approval import ApprovalGate
from tracing.task_trace import tracer

# Email configuration (update these or use environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")
RECIPIENT = "khilken1@gmail.com"


def generate_daily_summary() -> str:
    """Generate a text summary of today's activities."""
    today = date.today().isoformat()

    history = ImprovementHistory()
    proposal_store = ProposalStore()
    approval_gate = ApprovalGate()

    events = history.get_history()
    todays_events = [e for e in events if e.timestamp.startswith(today)]

    proposals = proposal_store.list_all()
    todays_proposals = [p for p in proposals if p.created_at.startswith(today)]

    pending = approval_gate.list_pending()

    summary = f"""
Daily Hermes Self-Improvement Summary
Date: {today}
=====================================

Activity Summary:
- Total events logged today: {len(todays_events)}
- New proposals generated: {len(todays_proposals)}
- Proposals pending review: {len(pending)}

Recent Activity:
"""

    for event in todays_events[-10:]:
        summary += f"  - [{event.timestamp[11:16]}] {event.event_type.value}\n"

    if todays_proposals:
        summary += "\nToday's Proposals:\n"
        for p in todays_proposals:
            summary += f"  - [{p.risk_level}] {p.title}\n"

    summary += "\nEnd of Daily Summary\n"
    return summary


def send_email(subject: str, body: str):
    """Send email using SMTP."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, RECIPIENT, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Fallback: print the summary
        print("\n--- EMAIL CONTENT (fallback) ---\n")
        print(body)


def main():
    print("Generating daily summary...")
    summary = generate_daily_summary()

    subject = f"Hermes Daily Summary - {date.today().isoformat()}"
    send_email(subject, summary)


if __name__ == "__main__":
    main()