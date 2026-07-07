# Hermes Memory Health Dashboard

A beautiful, self-contained dashboard for monitoring the health and state of Hermes' long-term memory system.

## Features

- **Live Auto-Refresh** — Automatically polls `memory_health.json` every 15s–2m (toggleable + smart pause when tab hidden)
- Real-time metrics (total memories, clusters, health score)
- Interactive charts (memory types, project distribution)
- Top tags visualization
- Recent high-value syntheses feed
- One-click actions to trigger MemorySynthesizer tasks (Advanced Clustering, Full Synthesis, Reflections, Health Reports)
- "Last updated" relative timestamp
- Fully responsive and modern UI

## How to Use (Recommended)

### Full Experience (Recommended)
1. Start the local dashboard server:
   ```bash
   python memory_dashboard/run_dashboard_server.py
   ```
2. Open: **http://localhost:8765/memory_health_dashboard.html**

3. (Optional but powerful) Start the scheduled exporter in another terminal:
   ```bash
   python memory_dashboard/schedule_memory_export.py
   ```

### Quick Start
Just open `memory_health_dashboard.html` directly (works, but server mode is better for live updates).

## Automation Recommendations

- Run `schedule_memory_export.py` in the background so the dashboard stays fresh.
- Integrate the exporter as a recurring task inside Hermes / MemorySynthesizer.
- The dashboard can trigger memory optimization tasks (visible in browser console for now; future versions will write to a shared task queue Hermes monitors).
- Action buttons in the UI trigger tasks via MCP to the MemorySynthesizer sub-agent

## Future Enhancements (Hermes can implement)

- Live auto-refresh
- Time-series memory growth charts
- Interactive cluster explorer
- One-click "Optimize Memory" that runs full clustering + synthesis pipeline
- Export to Obsidian notes

---

*Part of the Hermes self-sustaining personal AGI memory architecture.*