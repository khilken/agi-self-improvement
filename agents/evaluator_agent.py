"""
Evaluator Agent for Hermes (with Ollama support)
================================================

Evaluates outputs using a local LLM (Ollama) for scoring and feedback.
"""

import logging
import json
from typing import List, Dict, Any, Tuple

from mcp.protocol import BaseMCPAgent, MessageType, MCPMessage
from tracing.task_trace import tracer

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

logger = logging.getLogger("EvaluatorAgent")


class EvaluatorAgent(BaseMCPAgent):
    def __init__(self, name: str = "evaluator", model: str = "qwen2.5:32b"):
        super().__init__(name=name)
        self.model = model
        self.mcp.register_handler(MessageType.TASK_REQUEST, self.handle_task_request)

    def get_capabilities(self) -> List[str]:
        return [
            "output_evaluation",
            "quality_scoring",
            "feedback_generation",
            "reflection"
        ]

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
        if not OLLAMA_AVAILABLE:
            return 0.6, "Ollama not available - using default score."

        prompt = f"""You are an expert evaluator.

Task: {json.dumps(task, indent=2)}

Output to evaluate: {json.dumps(output, indent=2)}

Rate the output from 0.0 to 1.0 on quality, completeness, and correctness.
Respond ONLY with valid JSON:
{{"score": 0.85, "feedback": "Short explanation"}}"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json"
            )
            data = json.loads(response['message']['content'])
            return float(data.get("score", 0.6)), data.get("feedback", "No feedback.")
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return 0.5, f"Evaluation error: {str(e)}"

    def _generate_suggestions(self, score: float, feedback: str) -> List[str]:
        suggestions = []
        if score < 0.6:
            suggestions.append("Increase detail, structure, or accuracy.")
        return suggestions


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("EvaluatorAgent (LLM) ready.")