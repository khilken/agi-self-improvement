#!/bin/bash
# Stop Hermes Full Stack (Production Ready)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$PROJECT_DIR/.hermes_pids"
LOG_DIR="$PROJECT_DIR/logs"

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
    echo "No PID file found. Killing by process name..."
    pkill -f "run_dashboard_server.py" || true
    pkill -f "memory_synthesizer.py" || true
fi

echo "✅ Hermes stack stopped."
echo "Logs preserved in: $LOG_DIR"