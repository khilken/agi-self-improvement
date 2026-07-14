"""
Evaluator Agent for Hermes (Production LLM Version)
===================================================

Uses Ollama for high-quality output evaluation and reflection.
"""

from __future__ import annotations

import logging
import json
from typing import List, Dict, Tuple

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer

try:
    from config import get_ollama_client, OLLAMA_DEFAULT_MODEL, configure_ollama_env
    configure_ollama_env()
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False
    OLLAMA_DEFAULT_MODEL = "qwen2.5:32b"
    get_ollama_client = None  # type: ignore

logger = logging.getLogger("EvaluatorAgent")


class EvaluatorAgent(BaseMCPAgent):
    def __init__(self, name: str = "evaluator", model: str | None = None):
        super().__init__(name=name)
        self.model = model or OLLAMA_DEFAULT_MODEL
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return ["output_evaluation", "quality_scoring", "feedback_generation", "reflection"]

    def handle_task_request(self, msg: MCPMessage):
        context = msg.payload.get("context", {})
        original_output = context.get("output", {})
        original_task = context.get("original_task", {})
        trace_id = context.get("trace_id")

        score, feedback = self._evaluate_with_llm(original_output, original_task)

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

    def _evaluate_with_llm(self, output: Dict, task: Dict) -> Tuple[float, str]:
        if not OLLAMA_AVAILABLE or get_ollama_client is None:
            return 0.6, "Ollama not available."

        prompt = f"""You are a strict but fair evaluator of AI agent outputs.

TASK DESCRIPTION:
{json.dumps(task, indent=2)}

AGENT OUTPUT:
{json.dumps(output, indent=2)}

Evaluate the output on:
- Correctness (does it solve the task?)
- Completeness
- Clarity and structure
- Actionability

Respond ONLY with valid JSON:
{{"score": 0.0-1.0, "feedback": "One or two sentences explaining the score"}}"""

        try:
            client = get_ollama_client()
            response = client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json"
            )
            data = json.loads(response["message"]["content"])
            score = max(0.0, min(1.0, float(data.get("score", 0.6))))
            feedback = data.get("feedback", "No feedback provided.")
            return score, feedback
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return 0.5, f"Evaluation error: {str(e)}"

    def _generate_suggestions(self, score: float, feedback: str) -> List[str]:
        suggestions = []
        if score < 0.5:
            suggestions.append("Significantly improve detail, structure, or accuracy.")
        elif score < 0.7:
            suggestions.append("Add more depth or better formatting.")
        return suggestions
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    agent = EvaluatorAgent()
    from agents.base_runner import run_agent
    run_agent(agent)
