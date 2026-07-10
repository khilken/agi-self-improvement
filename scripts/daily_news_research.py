#!/usr/bin/env python3
"""
Daily News Research Cron Job
============================

Runs the News Research Agent for local (Grand Junction), national, and international news.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.dispatcher import HermesDispatcher
import logging

logging.basicConfig(level=logging.INFO)


def run_daily_news_research():
    print("\n=== Daily News Research ===\n")
    d = HermesDispatcher()

    print("[1/3] Researching local Grand Junction news...")
    d.dispatch("news_research", "research", {"scope": "local"})

    print("[2/3] Researching national news...")
    d.dispatch("news_research", "research", {"scope": "national"})

    print("[3/3] Researching international news...")
    d.dispatch("news_research", "research", {"scope": "international"})

    print("\nDaily news research complete.\n")


if __name__ == "__main__":
    run_daily_news_research()