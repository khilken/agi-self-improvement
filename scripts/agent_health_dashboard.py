#!/usr/bin/env python3
"""Simple Agent Health Dashboard"""
import os
from pathlib import Path

PID_FILE = Path("/Users/kevin/.hermes/self/.hermes_pids")

def main():
    print("=== Hermes Agent Health Dashboard ===\n")
    if not PID_FILE.exists():
        print("No PID file found. Stack may not be running.")
        return

    with open(PID_FILE) as f:
        for line in f:
            if ":" in line:
                name, pid = line.strip().split(":")
                running = os.path.exists(f"/proc/{pid}") if os.name == "posix" else True
                status = "RUNNING" if running else "STOPPED"
                print(f"{name:25} {pid:8} {status}")

if __name__ == "__main__":
    main()