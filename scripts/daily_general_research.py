#!/usr/bin/env python3
"""
Daily General Research Cron Job
================================

Runs web search and scraping for latest developments in AI, AGI, and tools.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.web_search_agent import WebSearchAgent
from agents.web_scraper_agent import WebScraperAgent
from agents.dispatcher import HermesDispatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DailyGeneralResearch")


def run_daily_general_research():
    print("\n=== Daily General Research ===\n")

    d = HermesDispatcher()

    # Web search for latest AGI research
    print("[1/3] Searching for latest AGI developments...")
    d.dispatch("web_search", "search", {"query": "latest AGI research papers tools 2026"})

    # Web search for new AI agent frameworks
    print("[2/3] Searching for new agent frameworks...")
    d.dispatch("web_search", "search", {"query": "new AI agent frameworks protocols 2026"})

    # Targeted scraping (example)
    print("[3/3] Scraping key research sites...")
    d.dispatch("web_scraper", "scrape", {
        "url": "https://arxiv.org/list/cs.AI/recent",
        "selector": "dt"
    })

    print("\nDaily general research complete.\n")


if __name__ == "__main__":
    run_daily_general_research()