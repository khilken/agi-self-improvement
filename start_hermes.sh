#!/bin/bash
# Hermes Full Stack Launcher (Production Ready)
# Usage: ./start_hermes.sh [--daemon]

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/.hermes_pids"

mkdir -p "$LOG_DIR"

echo "🚀 Starting Hermes Self-Sustaining AGI Stack..."
echo "Project: $PROJECT_DIR"
echo "Logs:    $LOG_DIR"
echo ""

# Function to start a component with logging
start_component() {
    local name=$1
    local cmd=$2
    local log_file="$LOG_DIR/${name}.log"

    echo "Starting $name..."
    if [ "$1" = "MemorySynthesizer" ]; then
        (cd "$PROJECT_DIR" && PYTHONPATH=. nohup $cmd > "$log_file" 2>&1) &
    else
        (cd "$PROJECT_DIR" && nohup $cmd > "$log_file" 2>&1) &
    fi
    local pid=$!
    echo "$name:$pid" >> "$PID_FILE"
    echo "  → PID: $pid | Log: $log_file"
}

# Clean old PID file
rm -f "$PID_FILE"

# Start components
start_component "Dashboard" "python memory_dashboard/run_dashboard_server.py"
start_component "MemorySynthesizer" "python agents/memory_synthesizer.py"

echo ""
echo "✅ Hermes stack started successfully!"
echo "Dashboard: http://localhost:8765/memory_health_dashboard.html"
echo ""
echo "To stop: ./stop_hermes.sh"
echo "Logs:    tail -f $LOG_DIR/*.log"
echo ""

# Optional daemon mode
if [[ "$1" == "--daemon" ]]; then
    echo "Running in daemon mode. Use ./stop_hermes.sh to stop."
    disown
fi
