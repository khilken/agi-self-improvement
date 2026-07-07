"""
Shared Task Queue for Hermes
============================

A simple, persistent, file-based task queue.
Perfect for communication between:
- Memory Health Dashboard
- Hermes main agent
- MemorySynthesizer
- Any other sub-agents or tools

Tasks are stored as individual JSON files in the `tasks/` directory.
This makes everything:
- Inspectable by humans
- Git-friendly
- Persistent across restarts
- Easy to debug

Task Structure:
{
    "id": "uuid",
    "task_type": "advanced_clustering" | "full_synthesis" | ...,
    "source": "memory_health_dashboard" | "hermes" | "user",
    "created_at": timestamp,
    "status": "pending" | "in_progress" | "completed" | "failed",
    "payload": {...},
    "result": {...} or null,
    "processed_at": timestamp or null
}
"""

import json
import uuid
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

TASKS_DIR = Path("tasks")
TASKS_DIR.mkdir(exist_ok=True)


def _get_task_path(task_id: str) -> Path:
    return TASKS_DIR / f"{task_id}.json"


def create_task(
    task_type: str,
    source: str = "unknown",
    payload: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new task and return its ID."""
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "task_type": task_type,
        "source": source,
        "created_at": time.time(),
        "status": "pending",
        "payload": payload or {},
        "result": None,
        "processed_at": None
    }
    
    path = _get_task_path(task_id)
    path.write_text(json.dumps(task, indent=2))
    return task_id


def list_pending_tasks() -> List[Dict[str, Any]]:
    """Return all tasks with status 'pending'."""
    tasks = []
    for file in TASKS_DIR.glob("*.json"):
        try:
            task = json.loads(file.read_text())
            if task.get("status") == "pending":
                tasks.append(task)
        except Exception:
            continue
    # Sort by creation time (oldest first)
    return sorted(tasks, key=lambda x: x.get("created_at", 0))


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific task by ID."""
    path = _get_task_path(task_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def claim_task(task_id: str) -> bool:
    """Mark a task as 'in_progress'. Returns True if successful."""
    task = get_task(task_id)
    if not task or task.get("status") != "pending":
        return False
    
    task["status"] = "in_progress"
    task["claimed_at"] = time.time()
    
    path = _get_task_path(task_id)
    path.write_text(json.dumps(task, indent=2))
    return True


def complete_task(task_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
    """Mark a task as completed with optional result."""
    task = get_task(task_id)
    if not task:
        return False
    
    task["status"] = "completed"
    task["result"] = result
    task["processed_at"] = time.time()
    
    path = _get_task_path(task_id)
    path.write_text(json.dumps(task, indent=2))
    return True


def fail_task(task_id: str, error: str) -> bool:
    """Mark a task as failed."""
    task = get_task(task_id)
    if not task:
        return False
    
    task["status"] = "failed"
    task["result"] = {"error": error}
    task["processed_at"] = time.time()
    
    path = _get_task_path(task_id)
    path.write_text(json.dumps(task, indent=2))
    return True


def cleanup_old_tasks(days: int = 7):
    """Remove completed/failed tasks older than X days."""
    cutoff = time.time() - (days * 86400)
    for file in TASKS_DIR.glob("*.json"):
        try:
            task = json.loads(file.read_text())
            if task.get("status") in ["completed", "failed"]:
                if task.get("processed_at", 0) < cutoff:
                    file.unlink()
        except Exception:
            continue


if __name__ == "__main__":
    print("Task Queue module loaded.")
    print(f"Tasks directory: {TASKS_DIR.resolve()}")