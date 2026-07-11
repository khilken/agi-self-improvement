#!/usr/bin/env python3
"""
Agent Health Check & Auto-Restart
=================================

Checks if Hermes agents are running and restarts them if needed.
"""

import os
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PID_FILE = PROJECT_DIR / ".hermes_pids"
START_SCRIPT = PROJECT_DIR / "start_hermes.sh"


def get_running_pids():
    if not PID_FILE.exists():
        return {}
    pids = {}
    with open(PID_FILE) as f:
        for line in f:
            if ":" in line:
                name, pid = line.strip().split(":", 1)
                try:
                    pids[name] = int(pid)
                except ValueError:
                    continue
    return pids


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def restart_stack():
    print("Restarting Hermes stack...")
    subprocess.run(["bash", str(START_SCRIPT)], check=True, cwd=str(PROJECT_DIR))


def main():
    pids = get_running_pids()
    if not pids:
        print("No PID file / no agents registered. Starting stack...")
        restart_stack()
        return

    dead_agents = []
    for name, pid in pids.items():
        if not is_process_running(pid):
            print(f"[WARN] {name} (PID {pid}) is not running")
            dead_agents.append(name)
        else:
            print(f"[OK]   {name} (PID {pid})")

    if dead_agents:
        print(f"Found {len(dead_agents)} dead agents. Restarting stack...")
        restart_stack()
    else:
        print("All agents are healthy.")


if __name__ == "__main__":
    main()
