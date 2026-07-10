#!/usr/bin/env python3
"""
Daily Self-Research Cron Job
============================

Researches and analyzes the Hermes system itself for improvement opportunities.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.self_research_agent import SelfResearchAgent
from agents.dispatcher import HermesDispatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DailySelfResearch")


def run_daily_self_research():
    print("\n=== Daily Self-Research ===\n")

    d = HermesDispatcher()

    print("[1/3] Analyzing Hermes traces and performance...")
    d.dispatch("self_research", "analyze", {"focus": "traces"})

    print("[2/3] Analyzing proposal quality...")
    d.dispatch("self_research", "analyze", {"focus": "proposals"})

    print("[3/3] Identifying improvement opportunities...")
    d.dispatch("self_research", "analyze", {"focus": "architecture"})

    print("\nDaily self-research complete.\n")


if __name__ == "__main__":
    run_daily_self_research()