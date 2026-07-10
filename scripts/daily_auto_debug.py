#!/usr/bin/env python3
"""
Daily Automatic Debug & Log Analysis Cron Job
==============================================

Analyzes logs, detects issues, and applies safe automatic fixes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.dispatcher import HermesDispatcher
import logging

logging.basicConfig(level=logging.INFO)


def run_daily_auto_debug():
    print("\n=== Daily Auto Debug & Log Analysis ===\n")
    d = HermesDispatcher()

    print("[1/3] Analyzing recent logs...")
    d.dispatch("auto_debug", "analyze", {"log_file": "logs/*.log"})

    print("[2/3] Detecting common errors...")
    d.dispatch("auto_debug", "analyze", {"focus": "errors"})

    print("[3/3] Applying safe automatic fixes...")
    d.dispatch("auto_debug", "fix", {"risk_level": "low"})

    print("\nDaily auto-debug complete.\n")


if __name__ == "__main__":
    run_daily_auto_debug()