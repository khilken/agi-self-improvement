"""
Model Preference System
=======================

Handles model selection and preference logic, including Fable 5 support.
"""

from enum import Enum
from typing import Dict, Any
import os


class ModelTier(str, Enum):
    LOCAL = "local"           # Ollama / local models
    STANDARD = "standard"     # Claude 4 / GPT-5 class
    FRONTIER = "frontier"     # Fable 5, Mythos 5, etc.


class ModelPreference:
    """
    Manages which model to use for different tasks.
    Fable 5 is preferred for complex orchestration and long-horizon work when available.
    """

    def __init__(self):
        self.default_model = os.getenv("HERMES_DEFAULT_MODEL", "claude-fable-5")
        self.fallback_model = os.getenv("HERMES_FALLBACK_MODEL", "qwen2.5:32b")
        self.fable5_available = self._check_fable5_availability()

    def _check_fable5_availability(self) -> bool:
        """Check if Fable 5 can be used (Anthropic key present and valid)."""
        # In production this would do a real availability check
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def get_model_for_task(self, task_type: str, complexity: str = "medium") -> str:
        """
        Select the best model for a given task.
        """
        if task_type in ["orchestration", "reflection", "meta_improvement"] and self.fable5_available:
            return "claude-fable-5"

        if complexity == "high" and self.fable5_available:
            return "claude-fable-5"

        if self.fable5_available:
            return "claude-fable-5"

        return self.fallback_model

    def get_preference_report(self) -> Dict[str, Any]:
        return {
            "fable5_available": self.fable5_available,
            "default_model": self.default_model,
            "fallback_model": self.fallback_model,
            "recommendation": "claude-fable-5" if self.fable5_available else self.fallback_model
        }