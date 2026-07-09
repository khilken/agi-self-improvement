#!/bin/bash
# Stop all Hermes processes

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/.hermes_pids"

echo "🛑 Stopping Hermes stack..."

if [ -f "$PID_FILE" ]; then
    while IFS=: read -r name pid; do
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Stopping $name (PID $pid)..."
            kill "$pid" 2>/dev/null || true
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
else
    echo "Killing by process name..."
    pkill -f "run_dashboard_server.py" || true
    pkill -f "memory_synthesizer.py" || true
    pkill -f "researcher_agent.py" || true
    pkill -f "coder_agent.py" || true
    pkill -f "evaluator_agent.py" || true
    pkill -f "meta_improver_agent.py" || true
    pkill -f "orchestrator_agent.py" || true
fi

echo "✅ Hermes stack stopped."