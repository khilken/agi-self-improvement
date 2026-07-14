"""
Cost Optimization Recommendations
=================================

Suggests the most cost-effective model for a given task.
"""


MODEL_COSTS = {
    "claude-fable-5": 0.015,
    "qwen2.5:32b": 0.0,      # Local
    "llama3.1:70b": 0.0,     # Local
}

def recommend_model(task_complexity: str, budget: str = "medium") -> str:
    if budget == "low" or task_complexity == "simple":
        return "qwen2.5:32b"
    return "claude-fable-5"