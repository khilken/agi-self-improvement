"""
Hermes Task Dispatcher
======================

Routes tasks to specialized sub-agents with automatic tracing and capability-aware routing.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp.protocol import MCPProtocol, MessageType
from tracing.task_trace import tracer
from tracing.model_preference import ModelPreference

logger = logging.getLogger("Dispatcher")


# Canonical agent registry: name -> capabilities
AGENT_REGISTRY: Dict[str, List[str]] = {
    "researcher": ["research", "web_research", "information_synthesis"],
    "coder": ["code", "implement", "refactor"],
    "memory_synthesizer": ["memory_synthesis", "consolidation", "health_report"],
    "orchestrator": ["orchestrate", "plan"],
    "evaluator": ["evaluate", "output_evaluation", "reflection"],
    "meta_improver": ["analyze_traces", "propose_improvements"],
    "hyper_meta_improver": ["hyper_meta", "improve_meta"],
    "web_search": ["web_search", "result_synthesis"],
    "web_scraper": ["web_scrape", "extract"],
    "self_research": ["self_research"],
    "arxiv_summarizer": ["arxiv_search", "paper_summarization"],
    "github_trending": ["github_trending"],
    "x_twitter_scanner": ["x_scan", "twitter"],
    "news_research": ["news", "local_news", "national_news"],
    "auto_debug": ["debug", "log_analysis"],
    "advanced_coding": ["advanced_code", "tdd"],
    "comprehensive_debug_testing": ["test", "coverage", "debug_test"],
    "knowledge_curator": ["knowledge", "deduplicate"],
    "safety_governance": ["safety", "risk_review"],
    "long_horizon_planner": ["plan_long", "goal_decompose"],
    "experimentation": ["experiment", "ab_test"],
    "self_verification": ["verify", "check_improvement"],
    "version_control_rollback": ["rollback", "version"],
    "resource_monitor": ["resource", "cost", "usage"],
    "external_integration": ["slack", "telegram", "notion", "email"],
    "opencrabs": [
        "opencrabs",
        "rust_agent_runtime",
        "a2a_gateway",
        "external_agent_runtime",
        "opencrabs_status",
        "opencrabs_doctor",
        "opencrabs_build",
        "opencrabs_run",
    ],
    "momo": [
        "momo",
        "ai_memory_system",
        "external_memory_service",
        "mcp_memory_server",
        "momo_status",
        "momo_doctor",
        "momo_build",
        "momo_health",
        "momo_document",
        "momo_documents",
        "momo_search",
        "momo_ingest",
    ],
    "awesome_llm_apps": [
        "awesome_llm_apps",
        "llm_app_templates",
        "agent_template_catalog",
        "awesome_llm_apps_status",
        "awesome_llm_apps_doctor",
        "awesome_llm_apps_list",
        "awesome_llm_apps_show",
        "awesome_llm_apps_setup",
        "awesome_llm_apps_run",
    ],
    "prefect": [
        "prefect",
        "workflow_orchestration",
        "flow_orchestration",
        "prefect_status",
        "prefect_doctor",
        "prefect_setup",
        "prefect_cli",
        "prefect_smoke",
        "prefect_server",
        "prefect_wait_ready",
    ],
    "project_nomad": [
        "project_nomad",
        "offline_knowledge_server",
        "offline_media_archives_data",
        "offline_ai_server",
        "nomad_status",
        "nomad_doctor",
        "nomad_render_compose",
        "nomad_compose_config",
        "nomad_setup",
        "nomad_build",
        "nomad_up",
        "nomad_down",
        "nomad_wait_ready",
    ],
}


class HermesDispatcher:
    def __init__(self, agent_name: str = "hermes_dispatcher"):
        self.mcp = MCPProtocol(agent_name=agent_name)
        self.model_pref = ModelPreference()
        # Keep backward-compatible map of known targets
        self.agents = {name: name for name in AGENT_REGISTRY}

    def resolve_agent(self, task_type: str, preferred: Optional[str] = None) -> str:
        """Pick an agent by explicit name or by capability match."""
        if preferred and preferred in self.agents:
            return preferred
        task_l = (task_type or "").lower()
        for name, caps in AGENT_REGISTRY.items():
            if task_l in caps or any(task_l in c for c in caps):
                return name
        # Heuristics
        if "research" in task_l or "search" in task_l:
            return "researcher"
        if "code" in task_l or "implement" in task_l:
            return "coder"
        if "eval" in task_l:
            return "evaluator"
        if "memory" in task_l or "synth" in task_l:
            return "memory_synthesizer"
        if "debug" in task_l or "test" in task_l:
            return "comprehensive_debug_testing"
        if "news" in task_l:
            return "news_research"
        if "opencrabs" in task_l or "a2a" in task_l or "rust_agent" in task_l:
            return "opencrabs"
        if "momo" in task_l or "memory_service" in task_l or "mcp_memory" in task_l:
            return "momo"
        if "awesome_llm" in task_l or "llm_app_template" in task_l or "agent_template" in task_l:
            return "awesome_llm_apps"
        if "prefect" in task_l or "workflow_orchestration" in task_l or "flow_orchestration" in task_l:
            return "prefect"
        if "project_nomad" in task_l or "nomad" in task_l or "offline_knowledge" in task_l or "offline_ai" in task_l:
            return "project_nomad"
        return preferred or "researcher"

    def dispatch(
        self,
        target_agent: str,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        resolved = self.resolve_agent(task_type, preferred=target_agent)
        if resolved not in self.agents:
            # Allow dispatch to unregistered but named agents (queues still work)
            logger.warning(f"Agent {resolved} not in registry; dispatching anyway")
            self.agents[resolved] = resolved

        context = context or {}

        # Preferred model annotation for downstream agents
        try:
            context.setdefault("preferred_model", self.model_pref.get_model_for_task(task_type))
        except Exception:
            pass

        trace_id = tracer.start_trace(
            task_type=task_type,
            agent=resolved,
            input_data=context,
        )
        context["trace_id"] = trace_id

        payload = {
            "task_type": task_type,
            "context": context,
        }

        logger.info(f"Dispatching {task_type} → {resolved} (trace={trace_id})")

        self.mcp.send(
            to_agent=resolved,
            msg_type=MessageType.TASK_REQUEST,
            payload=payload,
            correlation_id=correlation_id or trace_id,
        )
        return trace_id

    def dispatch_research(self, query: str):
        return self.dispatch("researcher", "research", {"query": query})

    def dispatch_coding(self, description: str):
        return self.dispatch("coder", "code", {"description": description})

    def dispatch_evaluation(self, output: Dict, original_task: Dict):
        return self.dispatch("evaluator", "evaluate", {
            "output": output,
            "original_task": original_task,
        })

    def dispatch_meta_analysis(self):
        return self.dispatch("meta_improver", "analyze_traces", {})

    def run_with_reflection(self, target_agent: str, task_type: str, context: Dict):
        """
        Executes a task with automatic reflection:
        1. Dispatch to target agent
        2. Dispatch evaluation to Evaluator
        3. Dispatch meta analysis to Meta-Improver
        """
        context = dict(context or {})
        trace_id = self.dispatch(target_agent, task_type, context)

        eval_context = {
            "original_task": context,
            "output": {"note": "pending agent result; evaluate intent/completeness"},
            "trace_id": trace_id,
        }
        self.dispatch("evaluator", "evaluate", eval_context)

        self.dispatch("meta_improver", "analyze_traces", {
            "trace_id": trace_id,
            "trigger": "run_with_reflection",
        })

        logger.info(f"Reflection loop initiated for trace {trace_id}")
        return {
            "trace_id": trace_id,
            "message": "Task + Evaluation + Meta-Improver dispatched. Reflection loop active.",
        }
