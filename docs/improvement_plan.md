# Hermes Maximum Improvement Plan (2026)

## Goal
Evolve Hermes into a fully autonomous, recursively self-improving multi-agent AGI system.

## Phased Roadmap

### Phase 1: Core Self-Improvement Loop (In Progress)
- [x] Structured Task Tracing
- [x] Reflection + Evaluator Agent
- [x] Meta-Improver Agent with persistence
- [x] Orchestrator Agent
- [x] Automatic tracing in Dispatcher
- [ ] Real LLM calls in Evaluator & Meta-Improver (partial)

### Phase 2: Advanced Self-Modification
- [ ] Meta-Improver proposes actual code/prompt diffs
- [ ] Safe auto-apply for low-risk improvements
- [ ] Improvement history + versioning

### Phase 3: Fable 5 Integration
- [ ] Detect Fable 5 availability
- [ ] Prefer Fable 5 for complex orchestration & long-horizon tasks
- [ ] Dynamic workflow support

### Phase 4: Observability & Marketplace
- [ ] Rich logging + dashboard
- [ ] Dynamic skill/tool registration & discovery
- [ ] Agent capability marketplace

### Phase 5: Safety & Governance
- [ ] Human-in-the-loop gates for self-modification
- [ ] Approval workflows for high-impact changes
- [ ] Rollback capability

## Multi-Agent Execution Strategy

| Agent | Responsibilities |
|-------|------------------|
| **Researcher** | Research new patterns, papers, protocols |
| **Coder** | Implement new agents, fix bugs, write tests |
| **Evaluator** | Score all outputs and improvement proposals |
| **Meta-Improver** | Analyze traces, generate improvement proposals |
| **Orchestrator** | Coordinate complex multi-step workflows |
| **Dispatcher** | Route work intelligently with tracing |

## Next Immediate Actions (Priority Order)
1. Make Evaluator & Meta-Improver use real LLM calls
2. Implement proposal application (safe auto-apply)
3. Add Fable 5 detection + preference
4. Build basic observability dashboard
5. Add Human-in-the-loop gates

---
*Last updated: July 2026*