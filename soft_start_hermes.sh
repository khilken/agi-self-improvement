#!/bin/bash
# Soft start — does NOT kill existing processes (safe for restricted shells)
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

export OLLAMA_HOST="${OLLAMA_HOST:-http://192.168.1.111:11434}"
export HERMES_DEFAULT_MODEL="${HERMES_DEFAULT_MODEL:-qwen2.5:32b}"
export PYTHONPATH="$PROJECT_DIR"

mkdir -p "$LOG_DIR"
: > "$PID_FILE"

cd "$PROJECT_DIR"

start_if_needed() {
  local name=$1
  local script=$2
  # Skip if a matching process already exists
  if pgrep -f "$script" >/dev/null 2>&1; then
    echo "  ↷ $name already running"
    local existing
    existing=$(pgrep -f "$script" | head -1)
    echo "$name:$existing" >> "$PID_FILE"
    return
  fi
  echo "  → Starting $name"
  "$PYTHON_BIN" "$script" >> "$LOG_DIR/${name}.log" 2>&1 &
  echo "$name:$!" >> "$PID_FILE"
}

echo "Soft-starting Hermes stack..."
echo "Ollama: $OLLAMA_HOST"
echo "Python: $PYTHON_BIN"

start_if_needed "Dashboard" "memory_dashboard/run_dashboard_server.py"
start_if_needed "MemorySynthesizer" "agents/memory_synthesizer.py"
start_if_needed "Researcher" "agents/researcher_agent.py"
start_if_needed "Coder" "agents/coder_agent.py"
start_if_needed "Evaluator" "agents/evaluator_agent.py"
start_if_needed "MetaImprover" "agents/meta_improver_agent.py"
start_if_needed "Orchestrator" "agents/orchestrator_agent.py"
start_if_needed "HyperMetaImprover" "agents/hyper_meta_improver_agent.py"
start_if_needed "OpenCRABS" "agents/opencrabs_agent.py"
start_if_needed "Momo" "agents/momo_agent.py"
start_if_needed "AwesomeLLMApps" "agents/awesome_llm_apps_agent.py"
start_if_needed "Prefect" "agents/prefect_agent.py"
start_if_needed "ProjectNomad" "agents/project_nomad_agent.py"

sleep 1
alive=0; total=0
while IFS=: read -r name pid; do
  total=$((total+1))
  if kill -0 "$pid" 2>/dev/null; then
    alive=$((alive+1))
    echo "  ✓ $name ($pid)"
  else
    echo "  ✗ $name ($pid) — see logs/${name}.log"
  fi
done < "$PID_FILE"

echo "Health: $alive / $total"
echo "Dashboard: http://localhost:8765/memory_health_dashboard.html"
