#!/usr/bin/env python3
"""
Scheduled Memory Health Exporter for Hermes
===========================================

Runs `export_memory_stats.py` on a configurable interval.
This keeps the Memory Health Dashboard continuously updated with fresh data.

Usage:
    python memory_dashboard/schedule_memory_export.py

    # Or run in background:
    nohup python memory_dashboard/schedule_memory_export.py &

You can also integrate this into Hermes/MemorySynthesizer as a recurring task.
"""

import time
import subprocess
import sys
from pathlib import Path

# Configuration
EXPORT_INTERVAL_SECONDS = 300          # 5 minutes (change as needed)
EXPORT_SCRIPT = "memory_dashboard/export_memory_stats.py"
LOG_FILE = "memory_dashboard/export.log"


def log(message: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_export():
    try:
        result = subprocess.run(
            [sys.executable, EXPORT_SCRIPT],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent  # Run from Hermes root
        )
        if result.returncode == 0:
            log("Memory stats exported successfully.")
        else:
            log(f"Export failed with code {result.returncode}")
            if result.stderr:
                log(result.stderr.strip())
    except Exception as e:
        log(f"Error running exporter: {e}")


if __name__ == "__main__":
    log("Starting scheduled memory health exporter...")
    log(f"Export interval: {EXPORT_INTERVAL_SECONDS} seconds ({EXPORT_INTERVAL_SECONDS/60:.1f} minutes)")

    while True:
        run_export()
        time.sleep(EXPORT_INTERVAL_SECONDS)