# Hermes Shared Task Queue

A lightweight, file-based task queue for communication between components of the Hermes system.

## Location
`tasks/` directory (JSON files)

## How it works

- Any component (Dashboard, Hermes, scripts, etc.) can create tasks by writing JSON files.
- The `MemorySynthesizer` (and potentially other agents) periodically checks for pending tasks and executes them.
- Tasks are atomic and persistent.

## Task Structure

```json
{
  "id": "uuid-string",
  "task_type": "advanced_clustering" | "full_synthesis" | "generate_reflection" | "health_report",
  "source": "memory_health_dashboard" | "hermes" | "user",
  "created_at": 1712345678.123,
  "status": "pending" | "in_progress" | "completed" | "failed",
  "payload": { ... optional data ... },
  "result": { ... filled after completion ... },
  "processed_at": timestamp or null
}
```

## Usage from Python

```python
from tasks.task_queue import create_task, list_pending_tasks

# Create a task (e.g. from the dashboard or a script)
task_id = create_task(
    task_type="advanced_clustering",
    source="memory_health_dashboard",
    payload={"n_results": 500}
)

# MemorySynthesizer will automatically pick it up
```

## Monitored By

- `MemorySynthesizer` sub-agent (checks every few seconds in its run loop)

## Benefits

- Simple and reliable
- Fully inspectable (just look at the JSON files)
- Works across processes and restarts
- No external dependencies (Redis, etc.)

This is the communication bridge between the visual dashboard and the autonomous memory maintenance system.