"""
Hermes project configuration
============================

Central defaults for Ollama, paths, and models.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root (this file lives at project root)
PROJECT_ROOT = Path(__file__).resolve().parent

# Ollama — user preference: local server on LAN, not localhost
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.1.111:11434")
OLLAMA_DEFAULT_MODEL = os.getenv("HERMES_DEFAULT_MODEL", "qwen2.5:32b")
OLLAMA_EMBED_MODEL = os.getenv("HERMES_EMBED_MODEL", "nomic-embed-text")

# MCP queues — single absolute location shared by all processes
MCP_QUEUES_DIR = Path(os.getenv("HERMES_MCP_QUEUES", str(Path.home() / ".hermes" / "mcp_queues")))

# Logs
LOG_DIR = PROJECT_ROOT / "logs"
PID_FILE = PROJECT_ROOT / ".hermes_pids"


def configure_ollama_env() -> str:
    """Ensure OLLAMA_HOST is set for the ollama Python client and CLI."""
    os.environ.setdefault("OLLAMA_HOST", OLLAMA_HOST)
    return os.environ["OLLAMA_HOST"]


def get_ollama_client():
    """Return an ollama Client pointed at the configured host."""
    configure_ollama_env()
    try:
        import ollama
        # Client accepts host= for remote servers
        return ollama.Client(host=OLLAMA_HOST)
    except Exception as e:
        raise RuntimeError(f"Failed to create Ollama client for {OLLAMA_HOST}: {e}") from e
