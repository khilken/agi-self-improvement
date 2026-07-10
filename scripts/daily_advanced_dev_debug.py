#!/usr/bin/env python3
"""
Daily Advanced Development & Debugging Cron Job
================================================

Runs the Advanced Coding Agent and Comprehensive Debugging & Testing Agent daily.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.dispatcher import HermesDispatcher
import logging

logging.basicConfig(level=logging.INFO)


def run_daily_advanced_dev_debug():
    print("\n=== Daily Advanced Dev & Debug ===\n")
    d = HermesDispatcher()

    print("[1/4] Running Advanced Coding Agent...")
    d.dispatch("advanced_coding", "refactor", {"type": "multi_file"})

    print("[2/4] Running Comprehensive Debug & Testing Agent...")
    d.dispatch("comprehensive_debug_testing", "analyze", {"focus": "coverage"})

    print("[3/4] Generating tests and fixes...")
    d.dispatch("comprehensive_debug_testing", "fix", {"risk_level": "low"})

    print("[4/4] Running verification experiments...")
    d.dispatch("experimentation", "test", {"type": "improvement_validation"})

    print("\nDaily advanced dev & debug complete.\n")


if __name__ == "__main__":
    run_daily_advanced_dev_debug()