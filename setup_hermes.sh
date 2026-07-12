#!/bin/bash
# Hermes One-Command Setup Script
# ===============================
# Safe macOS/Linux setup using a project virtualenv. Does not install into the
# externally-managed system Python.

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -n "${PYTHON_BIN:-}" ]; then
    PYTHON_BIN="$PYTHON_BIN"
elif command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
else
    PYTHON_BIN="python3"
fi
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/.venv}"
OLLAMA_HOST="${OLLAMA_HOST:-http://192.168.1.111:11434}"
HERMES_DEFAULT_MODEL="${HERMES_DEFAULT_MODEL:-qwen2.5:32b}"
ORIGINAL_PYTHONPATH="${PYTHONPATH:-}"

# Keep setup hermetic. Hermes desktop sessions can inject the global Hermes
# source tree and venv into PYTHONPATH; if pip sees those paths, it may skip
# installing dependencies into this project's .venv.
unset PYTHONPATH

printf "%b\n" "$BLUE"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           HERMES - Self-Sustaining Personal AGI            ║"
echo "║                    One-Command Setup                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
printf "%b\n" "$NC"

if [ ! -f "Hermes_System_Prompt.md" ]; then
    printf "%bError: Please run this script from inside the Hermes project directory.%b\n" "$RED" "$NC"
    exit 1
fi
printf "%b✓ Project directory: %s%b\n" "$GREEN" "$PROJECT_DIR" "$NC"

printf "\n%b[1/6] Checking Python...%b\n" "$BLUE" "$NC"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    printf "%bPython not found: %s%b\n" "$RED" "$PYTHON_BIN" "$NC"
    exit 1
fi
"$PYTHON_BIN" --version

printf "\n%b[2/6] Creating/updating virtualenv...%b\n" "$BLUE" "$NC"
if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel

printf "\n%b[3/6] Installing Python dependencies...%b\n" "$BLUE" "$NC"
if [ ! -f requirements.txt ]; then
    printf "%brequirements.txt missing%b\n" "$RED" "$NC"
    exit 1
fi
python -m pip install -r requirements.txt

printf "\n%b[4/6] Checking Ollama endpoint...%b\n" "$BLUE" "$NC"
if [ -n "$ORIGINAL_PYTHONPATH" ]; then
    export PYTHONPATH="$PROJECT_DIR:$ORIGINAL_PYTHONPATH"
else
    export PYTHONPATH="$PROJECT_DIR"
fi
export OLLAMA_HOST HERMES_DEFAULT_MODEL
python - <<'PY'
import os, sys, urllib.request, json
host = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434').rstrip('/')
try:
    with urllib.request.urlopen(host + '/api/tags', timeout=5) as resp:
        data = json.loads(resp.read().decode())
    models = [m.get('name') for m in data.get('models', [])]
    print(f"✓ Ollama reachable: {host}")
    print("  Models:", ", ".join(models[:10]) or "none listed")
except Exception as exc:
    print(f"⚠ Ollama not reachable at {host}: {exc}")
    print("  Setup can continue; model-dependent agents will use fallbacks until Ollama is reachable.")
PY

if command -v ollama >/dev/null 2>&1; then
    printf "\n%b[optional] Ensuring embedding model exists locally...%b\n" "$BLUE" "$NC"
    OLLAMA_HOST="$OLLAMA_HOST" ollama pull nomic-embed-text || printf "%bCould not pull nomic-embed-text; continuing.%b\n" "$YELLOW" "$NC"
else
    printf "%bollama CLI not found locally; using remote endpoint only.%b\n" "$YELLOW" "$NC"
fi

printf "\n%b[5/6] Creating runtime directories...%b\n" "$BLUE" "$NC"
mkdir -p tasks memory/vector_db mcp/queues logs logs/traces logs/improvements logs/approvals logs/history logs/backups
printf "%b✓ Runtime directories ready%b\n" "$GREEN" "$NC"

printf "\n%b[6/6] Running verification checks...%b\n" "$BLUE" "$NC"
python scripts/run_tests.py --no-pytest

printf "\n%b════════════════════════════════════════════════════════════%b\n" "$GREEN" "$NC"
printf "%b           Hermes setup complete%b\n" "$GREEN" "$NC"
printf "%b════════════════════════════════════════════════════════════%b\n" "$GREEN" "$NC"
echo ""
echo "Activate environment:"
echo "  source '$VENV_DIR/bin/activate'"
echo ""
echo "Start stack:"
echo "  ./soft_start_hermes.sh"
echo ""
echo "Dashboard:"
echo "  http://localhost:8765/memory_health_dashboard.html"
echo ""
echo "Ollama endpoint: $OLLAMA_HOST"
echo "Default model:   $HERMES_DEFAULT_MODEL"
