#!/bin/bash
# Hermes Full Stack Launcher (Production Ready)
# Starts all core + specialized agents

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
PID_FILE="$PROJECT_DIR/.hermes_pids"

mkdir -p "$LOG_DIR"

echo "🚀 Starting Full Hermes Multi-Agent Stack..."
echo "Project: $PROJECT_DIR"
echo ""

start_component() {
    local name=$1
    local cmd=$2
    local log_file="$LOG_DIR/${name}.log"

    echo "Starting $name..."
    (cd "$PROJECT_DIR" && PYTHONPATH=. nohup $cmd > "$log_file" 2>&1) &
    local pid=$!
    echo "$name:$pid" >> "$PID_FILE"
    echo "  → PID: $pid"
}

rm -f "$PID_FILE"

# Core agents
start_component "Dashboard" "python memory_dashboard/run_dashboard_server.py"
start_component "MemorySynthesizer" "python agents/memory_synthesizer.py"

# New specialized agents
start_component "Researcher" "python agents/researcher_agent.py"
start_component "Coder" "python agents/coder_agent.py"
start_component "Evaluator" "python agents/evaluator_agent.py"
start_component "MetaImprover" "python agents/meta_improver_agent.py"
start_component "Orchestrator" "python agents/orchestrator_agent.py"

echo ""
echo "✅ All agents started!"
echo "Dashboard: http://localhost:8765/memory_health_dashboard.html"
echo "To stop: ./stop_hermes.sh"
echo ""