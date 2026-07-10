#!/usr/bin/env python3
"""
Daily Specialized Research Cron Job
====================================

Runs arXiv summarizer, GitHub trending monitor, and X/Twitter scanner.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.dispatcher import HermesDispatcher
import logging

logging.basicConfig(level=logging.INFO)


def run_daily_specialized_research():
    print("\n=== Daily Specialized Research ===\n")
    d = HermesDispatcher()

    print("[1/4] arXiv paper summarization...")
    d.dispatch("arxiv_summarizer", "summarize", {"query": "AI agents self-improvement"})

    print("[2/4] GitHub trending monitor...")
    d.dispatch("github_trending", "trending", {"topic": "ai-agents"})

    print("[3/4] X/Twitter scanner...")
    d.dispatch("x_twitter_scanner", "scan", {"query": "AGI agents"})

    print("[4/4] Research synthesis...")
    d.dispatch("web_search", "search", {"query": "synthesis of latest AI research"})

    print("\nDaily specialized research complete.\n")


if __name__ == "__main__":
    run_daily_specialized_research()