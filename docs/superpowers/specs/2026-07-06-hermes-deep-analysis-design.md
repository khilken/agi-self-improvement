# Hermes Deep Analysis & Repair — Design

**Date:** 2026-07-06
**Status:** Approved

## Goal

Understand the entire Hermes codebase line-by-line, verify every module actually
runs, fix all defects automatically with verification after each change, then do
an efficiency/quality pass. Finish with an interactive knowledge-graph dashboard
of the final architecture.

## Scope

The `self/` repo: 12 Python files (~2,000 lines) across `vector_memory/`,
`agents/`, `mcp/`, `tasks/`, `memory_dashboard/`, plus `setup_hermes.sh`,
`Hermes_System_Prompt.md`, and per-module READMEs.

Out of scope: ChromaDB data in `memory/vector_db/` (treated as data, never
modified), unrelated refactors, new features.

## Phases

### Phase 1 — Full read & architecture map
Read every source file, script, and doc completely. Produce:
- Architecture summary: purpose of each module and the dependency graph
  (vector_memory ↔ agents/memory_synthesizer ↔ mcp ↔ tasks ↔ memory_dashboard).
- External dependency inventory (ChromaDB, embedding model, etc.).
- Defect list ranked by severity: broken imports, API misuse, logic bugs,
  dead code, README/code mismatches.

### Phase 2 — Environment & execution verification
- Create a virtual env at `~/.venvs/hermes` (outside OneDrive to avoid sync
  churn), install dependencies.
- Execute every module: import checks, each script entry point, dashboard
  server. Log every failure with its traceback into the defect list.

### Phase 3 — Fix loop
Work the defect list highest-severity first. For each fix:
1. Make the change.
2. Re-run the affected module.
3. Re-run previously-passing modules to catch regressions.
4. Commit with a descriptive message.

Add lightweight smoke tests where behavior is nontrivial: vector memory CRUD,
task queue ordering, MCP message routing.

### Phase 4 — Quality & efficiency pass
With everything running, review the full codebase for inefficiencies
(re-embedding on every call, O(n²) clustering, blocking I/O in loops, etc.).
Apply fixes, re-verify all modules, commit.

### Phase 5 — Knowledge graph dashboard
Run `understand-anything:understand` on the finished codebase to generate the
interactive dashboard, so the artifact reflects the repaired architecture.

## Constraints

- All changes committed to the existing git repo in small, revertible steps.
- Project stays at its OneDrive path; only the venv lives outside it.
- No destructive operations on existing memory data.

## Success criteria

- Every module imports and its entry point runs without error.
- Smoke tests pass for vector memory, task queue, and MCP routing.
- Defect list fully worked or each remaining item explicitly deferred with a reason.
- Knowledge-graph dashboard generated from the repaired code.
