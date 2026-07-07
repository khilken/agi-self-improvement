#!/bin/bash
#
# Hermes One-Command Setup Script
# ===============================
#
# This script sets up the complete Hermes self-improving memory system.
#
# Usage:
#   chmod +x setup_hermes.sh
#   ./setup_hermes.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           HERMES - Self-Sustaining Personal AGI            ║"
echo "║                    One-Command Setup                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running from correct directory
if [ ! -f "Hermes_System_Prompt.md" ]; then
    echo -e "${RED}Error: Please run this script from inside the Hermes/ directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Running from Hermes directory${NC}"

# ============================================
# 1. Check for Ollama
# ============================================
echo -e "\n${BLUE}[1/5] Checking for Ollama...${NC}"

if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Ollama not found.${NC}"
    echo "Please install Ollama first:"
    echo "  → https://ollama.com/download"
    echo ""
    read -p "Have you installed Ollama? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Please install Ollama and run this script again.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ollama is installed${NC}"
fi

# ============================================
# 2. Install Python Dependencies
# ============================================
echo -e "\n${BLUE}[2/5] Installing Python dependencies...${NC}"

pip install --upgrade pip > /dev/null 2>&1

PACKAGES=(
    "chromadb"
    "ollama"
    "hdbscan"
    "umap-learn"
    "scikit-learn"
    "numpy"
)

for package in "${PACKAGES[@]}"; do
    echo -e "  Installing ${package}..."
    pip install "$package" --quiet
done

echo -e "${GREEN}✓ All Python packages installed${NC}"

# ============================================
# 3. Pull Required Ollama Models
# ============================================
echo -e "\n${BLUE}[3/5] Pulling required Ollama models...${NC}"

echo -e "  Pulling nomic-embed-text (for embeddings)..."
ollama pull nomic-embed-text

echo -e "  Pulling qwen2.5:32b (recommended reasoning model)..."
ollama pull qwen2.5:32b || echo -e "${YELLOW}Warning: Could not pull qwen2.5:32b. You can pull it manually later.${NC}"

echo -e "${GREEN}✓ Ollama models ready${NC}"

# ============================================
# 4. Create necessary directories
# ============================================
echo -e "\n${BLUE}[4/5] Creating directories...${NC}"

mkdir -p tasks
mkdir -p memory/vector_db

echo -e "${GREEN}✓ Directories created${NC}"

# ============================================
# 5. Final Instructions
# ============================================
echo -e "\n${BLUE}[5/5] Setup Complete!${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           Hermes is ready to use!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Recommended way to run Hermes:"
echo ""
echo -e "${YELLOW}Terminal 1 - Dashboard Server:${NC}"
echo "  python memory_dashboard/run_dashboard_server.py"
echo ""
echo -e "${YELLOW}Terminal 2 - Auto Data Updates:${NC}"
echo "  python memory_dashboard/schedule_memory_export.py"
echo ""
echo -e "${YELLOW}Terminal 3 - MemorySynthesizer (with Task Queue):${NC}"
echo "  python agents/memory_synthesizer.py"
echo ""
echo "Then open your browser at:"
echo -e "${BLUE}http://localhost:8765/memory_health_dashboard.html${NC}"
echo ""
echo "You can now click buttons like 'Optimize Memory' in the dashboard"
echo "and the MemorySynthesizer will automatically process them."
echo ""
echo -e "${GREEN}Happy building!${NC}"
echo ""