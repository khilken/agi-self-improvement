# Hermes - Self-Sustaining Personal AGI

**Version:** 1.5  
**Date:** June 27, 2026  
**Owner:** Kevin

## Project Structure

```
Hermes/
├── Hermes_System_Prompt.md          # Main system prompt for Hermes
├── agents/
│   ├── memory_synthesizer.py        # Memory maintenance sub-agent
│   └── README.md
├── mcp/
│   ├── protocol.py                  # Multi-Agent Communication Protocol
│   └── ...
├── vector_memory/
│   ├── vector_memory.py             # Persistent semantic memory (ChromaDB)
│   ├── semantic_clustering.py       # Advanced HDBSCAN + UMAP clustering
│   └── ...
├── memory_dashboard/
│   ├── memory_health_dashboard.html # Live visual dashboard
│   ├── run_dashboard_server.py      # Local HTTP server
│   ├── schedule_memory_export.py    # Auto-updates dashboard data
│   └── ...
├── tasks/
│   ├── task_queue.py                # Shared file-based task queue
│   └── README.md
└── README.md                        # This file
```

## Quick Start (Recommended)

Run the one-command setup script:

```bash
chmod +x setup_hermes.sh
./setup_hermes.sh
```

This will automatically install dependencies and pull models.

After it finishes, follow the instructions it prints to start the three core components.

---

## Quick Start (Manual)

### 1. Install Dependencies

```bash
pip install chromadb ollama hdbscan umap-learn scikit-learn
ollama pull nomic-embed-text
ollama pull qwen2.5:32b   # or your preferred model
```

### 2. Recommended Way to Run

**Terminal 1 - Dashboard Server**
```bash
python memory_dashboard/run_dashboard_server.py
# Open http://localhost:8765/memory_health_dashboard.html
```

**Terminal 2 - Scheduled Data Updates**
```bash
python memory_dashboard/schedule_memory_export.py
```

**Terminal 3 - MemorySynthesizer (with Shared Task Queue)**
```bash
python agents/memory_synthesizer.py
```

### 3. Using the Dashboard

- Click buttons like **"Optimize Memory"** to trigger advanced clustering + synthesis.
- Tasks are created in the `tasks/` folder.
- `MemorySynthesizer` automatically picks them up and executes them.

## Core Components

- **Hermes_System_Prompt.md** — The brain of the main agent
- **MCP** — Communication protocol between agents
- **Vector Memory + Semantic Clustering** — Long-term knowledge + crystallization
- **MemorySynthesizer** — Active memory maintenance
- **Memory Health Dashboard** — Visual monitoring + control
- **Shared Task Queue** — Decoupled communication between dashboard and agents

## Philosophy

This project follows a **local-first, persistent, inspectable** approach:
- Everything runs locally (Ollama + ChromaDB)
- State is stored in files (easy to inspect and version)
- Agents communicate via MCP and a shared file-based task queue
- The system is designed to become increasingly autonomous over time

## Next Evolution Ideas

- Main Hermes supervisor/runner
- Historical memory metrics + trend charts
- More specialized sub-agents (Researcher, Coder, etc.)
- WebSocket live updates for the dashboard

---

**This is your complete Hermes self-improving memory architecture.**