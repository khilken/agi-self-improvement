"""
Test Script: Full Reflection Loop
=================================

Tests the complete flow:
Task → Dispatcher (with tracing) → Agent → Evaluator → Trace saved
"""

from agents.dispatcher import HermesDispatcher
from pathlib import Path

def main():
    print("=== Testing Hermes Reflection Loop ===\n")

    d = HermesDispatcher()

    # Test 1: Research task with reflection
    print("1. Dispatching research task with reflection...")
    result = d.run_with_reflection(
        target_agent="researcher",
        task_type="research",
        context={"query": "Latest AGI self-improvement techniques 2026"}
    )
    print(f"   Trace ID: {result['trace_id']}")
    print(f"   Message:  {result['message']}\n")

    # Test 2: Coding task with reflection
    print("2. Dispatching coding task with reflection...")
    result2 = d.run_with_reflection(
        target_agent="coder",
        task_type="code",
        context={"description": "Create a simple FastAPI health check endpoint"}
    )
    print(f"   Trace ID: {result2['trace_id']}\n")

    # Test 3: Direct evaluation dispatch
    print("3. Dispatching direct evaluation...")
    trace_id3 = d.dispatch_evaluation(
        output={"code": "def health(): return {'status': 'ok'}"},
        original_task={"description": "Create health endpoint"}
    )
    print(f"   Trace ID: {trace_id3}\n")

    # Check traces
    print("4. Checking saved traces...")
    traces_dir = Path("logs/traces")
    if traces_dir.exists():
        trace_files = list(traces_dir.glob("*.json"))
        print(f"   Found {len(trace_files)} trace file(s)")
        for f in trace_files[-3:]:  # Show last 3
            print(f"   - {f.name}")
    else:
        print("   No traces directory found yet.")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()