"""
Evaluator Agent for Hermes
==========================

Specialized agent that evaluates outputs from other agents
using structured scoring and feedback (Reflection Pattern).
"""

import logging
from typing import List, Dict, Any

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer

logger = logging.getLogger("EvaluatorAgent")


class EvaluatorAgent(BaseMCPAgent):
    """Agent that evaluates task outputs and provides feedback."""

    def __init__(self, name: str = "evaluator"):
        super().__init__(name=name)
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "output_evaluation",
            "quality_scoring",
            "feedback_generation",
            "reflection"
        ]

    def handle_task_request(self, msg: MCPMessage):
        task_type = msg.payload.get("task_type", "evaluate")
        context = msg.payload.get("context", {})

        original_output = context.get("output", {})
        original_task = context.get("original_task", {})
        trace_id = context.get("trace_id")

        logger.info(f"Evaluator received task: {task_type}")

        # Simple evaluation logic (can be enhanced with LLM calls later)
        score, feedback = self._evaluate_output(original_output, original_task)

        if trace_id:
            tracer.add_evaluation(trace_id, score, feedback)

        result = {
            "status": "completed",
            "score": score,
            "feedback": feedback,
            "suggestions": self._generate_suggestions(score, feedback)
        }

        self.mcp.send_message(
            to=msg.from_agent,
            message_type=MessageType.TASK_RESULT,
            payload=result,
            correlation_id=msg.correlation_id
        )

    def _evaluate_output(self, output: Dict, task: Dict) -> tuple[float, str]:
        """Basic evaluation logic. Replace with LLM call for better results."""
        score = 0.7  # Default neutral score
        feedback = "Output appears reasonable."

        # Example heuristics
        if not output:
            score = 0.2
            feedback = "Output is empty or missing."
        elif isinstance(output, dict) and len(output) < 2:
            score = 0.5
            feedback = "Output is minimal. Consider adding more detail."

        return score, feedback

    def _generate_suggestions(self, score: float, feedback: str) -> List[str]:
        suggestions = []
        if score < 0.6:
            suggestions.append("Increase detail and structure in the output.")
        if score < 0.4:
            suggestions.append("Review input requirements and re-process the task.")
        return suggestions


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("EvaluatorAgent ready. Use HermesDispatcher to send tasks.")