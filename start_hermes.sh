#!/bin/bash
# Hermes Full Stack Launcher - Robust Version
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/.hermes_pids"
PYTHON_BIN="${PYTHON_BIN:-$PROJECT_DIR/.venv/bin/python}"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Python runtime not found: $PYTHON_BIN"
    echo "Run: PYTHON_BIN=python3.11 ./setup_hermes.sh"
    exit 1
fi

# Point all agents at the LAN Ollama server (not localhost)
export OLLAMA_HOST="${OLLAMA_HOST:-http://192.168.1.111:11434}"
export HERMES_DEFAULT_MODEL="${HERMES_DEFAULT_MODEL:-qwen2.5:32b}"
export PYTHONPATH="$PROJECT_DIR"

mkdir -p "$LOG_DIR"

echo "🧹 Cleaning up old Hermes processes..."
pkill -f "run_dashboard_server.py" 2>/dev/null || true
pkill -f "memory_synthesizer.py" 2>/dev/null || true
pkill -f "researcher_agent.py" 2>/dev/null || true
pkill -f "coder_agent.py" 2>/dev/null || true
pkill -f "evaluator_agent.py" 2>/dev/null || true
pkill -f "meta_improver_agent.py" 2>/dev/null || true
pkill -f "orchestrator_agent.py" 2>/dev/null || true
pkill -f "hyper_meta_improver_agent.py" 2>/dev/null || true
sleep 2

rm -f "$PID_FILE"
touch "$PID_FILE"

echo "🚀 Starting Full Hermes Multi-Agent Stack..."
echo "Project: $PROJECT_DIR"
echo "Ollama:  $OLLAMA_HOST"
echo "Python:  $PYTHON_BIN"
echo ""

start_component() {
    local name=$1
    local script=$2
    local log_file="$LOG_DIR/${name}.log"

    echo "Starting $name..."
    # Use nohup + background without subshell so we capture the real python PID
    nohup "$PYTHON_BIN" "$script" > "$log_file" 2>&1 &
    local pid=$!
    echo "$name:$pid" >> "$PID_FILE"
    echo "  → PID: $pid"
    sleep 0.3
}

cd "$PROJECT_DIR"

# Core agents
start_component "Dashboard" "memory_dashboard/run_dashboard_server.py"
start_component "MemorySynthesizer" "agents/memory_synthesizer.py"

# Specialized agents with run loops
start_component "Researcher" "agents/researcher_agent.py"
start_component "Coder" "agents/coder_agent.py"
start_component "Evaluator" "agents/evaluator_agent.py"
start_component "MetaImprover" "agents/meta_improver_agent.py"
start_component "Orchestrator" "agents/orchestrator_agent.py"
start_component "HyperMetaImprover" "agents/hyper_meta_improver_agent.py"

echo ""
echo "✅ All agents started successfully!"
echo "Dashboard: http://localhost:8765/memory_health_dashboard.html"
echo "PID file:  $PID_FILE"
echo "To stop:   ./stop_hermes.sh"
echo ""

# Quick health sample
sleep 1
alive=0
total=0
while IFS=: read -r name pid; do
    total=$((total + 1))
    if kill -0 "$pid" 2>/dev/null; then
        alive=$((alive + 1))
    else
        echo "⚠️  $name (PID $pid) exited early — check logs/$name.log"
    fi
done < "$PID_FILE"
echo "Health: $alive / $total processes still alive"
