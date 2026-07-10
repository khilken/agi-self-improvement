"""
Hermes Task Dispatcher
======================

Routes tasks to specialized sub-agents with automatic tracing.
"""

import logging
from typing import Any, Dict, Optional

from mcp.protocol import MCPProtocol, MessageType
from tracing.task_trace import tracer

logger = logging.getLogger("Dispatcher")


class HermesDispatcher:
    def __init__(self, agent_name: str = "hermes_dispatcher"):
        self.mcp = MCPProtocol(agent_name=agent_name)
        self.agents = {
            "researcher": "researcher",
            "coder": "coder",
            "memory_synthesizer": "memory_synthesizer",
            "orchestrator": "orchestrator",
            "evaluator": "evaluator",
            "meta_improver": "meta_improver",
        }

    def dispatch(
        self,
        target_agent: str,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        if target_agent not in self.agents:
            logger.warning(f"Unknown agent: {target_agent}")
            return None

        context = context or {}

        # Start trace automatically
        trace_id = tracer.start_trace(
            task_type=task_type,
            agent=target_agent,
            input_data=context,
        )
        context["trace_id"] = trace_id

        payload = {
            "task_type": task_type,
            "context": context,
        }

        logger.info(f"Dispatching {task_type} to {target_agent} (trace={trace_id})")

        self.mcp.send(
            to_agent=target_agent,
            msg_type=MessageType.TASK_REQUEST,
            payload=payload,
            correlation_id=correlation_id,
        )
        return trace_id

    def dispatch_research(self, query: str):
        return self.dispatch("researcher", "research", {"query": query})

    def dispatch_coding(self, description: str):
        return self.dispatch("coder", "code", {"description": description})

    def dispatch_evaluation(self, output: Dict, original_task: Dict):
        return self.dispatch("evaluator", "evaluate", {
            "output": output,
            "original_task": original_task
        })

    def dispatch_meta_analysis(self):
        return self.dispatch("meta_improver", "analyze_traces", {})

        def run_with_reflection(self, target_agent: str, task_type: str, context: Dict):
            """
            Executes a task with automatic reflection:
            1. Dispatch to target agent
            2. Automatically dispatch evaluation request to Evaluator
            3. Return trace_id for tracking
            """
            trace_id = self.dispatch(target_agent, task_type, context)

            # Automatically dispatch to Evaluator with the trace_id
            eval_context = {
                "original_task": context,
                "trace_id": trace_id
            }
            self.dispatch("evaluator", "evaluate", eval_context)

            logger.info(f"Reflection loop initiated for trace {trace_id}")

            return {
                "trace_id": trace_id,
                "message": "Task + Evaluation dispatched. Reflection loop active."
            }
