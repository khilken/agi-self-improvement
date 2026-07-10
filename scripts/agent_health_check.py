#!/usr/bin/env python3
"""
Agent Health Check & Auto-Restart
=================================

Checks if Hermes agents are running and restarts them if needed.
"""

import os
import signal
import subprocess
from pathlib import Path

PID_FILE = Path("/Users/kevin/.hermes/self/.hermes_pids")
START_SCRIPT = Path("/Users/kevin/.hermes/self/start_hermes.sh")


def get_running_pids():
    if not PID_FILE.exists():
        return {}
    pids = {}
    with open(PID_FILE) as f:
        for line in f:
            if ":" in line:
                name, pid = line.strip().split(":")
                pids[name] = int(pid)
    return pids


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def restart_stack():
    print("Restarting Hermes stack...")
    subprocess.run(["bash", str(START_SCRIPT)], check=True)


def main():
    pids = get_running_pids()
    dead_agents = []

    for name, pid in pids.items():
        if not is_process_running(pid):
            print(f"[WARN] {name} (PID {pid}) is not running")
            dead_agents.append(name)

    if dead_agents:
        print(f"Found {len(dead_agents)} dead agents. Restarting stack...")
        restart_stack()
    else:
        print("All agents are healthy.")


if __name__ == "__main__":
    main()