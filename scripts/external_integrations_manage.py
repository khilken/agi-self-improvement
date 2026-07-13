#!/usr/bin/env python3
"""Unified status and diagnostics for Hermes-managed external integrations.

This script is intentionally light-weight: it imports only Hermes wrapper managers
and asks each integration for non-mutating status/doctor data. Use it as a single
operator entrypoint after adding or updating external runtimes.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Callable

from scripts import awesome_llm_apps_manage, momo_manage, opencrabs_manage, prefect_manage

INTEGRATIONS: dict[str, dict[str, Callable[[], dict[str, Any]]]] = {
    "opencrabs": {
        "status": opencrabs_manage.status,
        "doctor": opencrabs_manage.doctor,
    },
    "momo": {
        "status": momo_manage.status,
        "doctor": momo_manage.doctor,
    },
    "awesome-llm-apps": {
        "status": awesome_llm_apps_manage.status,
        "doctor": awesome_llm_apps_manage.doctor,
    },
    "prefect": {
        "status": prefect_manage.status,
        "doctor": prefect_manage.doctor,
    },
}


def _call_safely(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except Exception as exc:  # pragma: no cover - defensive operator boundary
        return {
            "ok": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
        }


def status() -> dict[str, Any]:
    integrations = {name: _call_safely(ops["status"]) for name, ops in INTEGRATIONS.items()}
    source_ready = {
        name: bool(info.get("source_exists") and info.get("source_commit") == info.get("pinned_commit"))
        for name, info in integrations.items()
    }
    return {
        "ok": all(source_ready.values()),
        "integration_count": len(integrations),
        "source_ready": source_ready,
        "integrations": integrations,
    }


def doctor() -> dict[str, Any]:
    diagnostics = {name: _call_safely(ops["doctor"]) for name, ops in INTEGRATIONS.items()}
    issues = []
    warnings = []
    for name, result in diagnostics.items():
        for issue in result.get("issues", []) or []:
            issues.append(f"{name}: {issue}")
        for warning in result.get("warnings", []) or []:
            warnings.append(f"{name}: {warning}")
        if result.get("error"):
            issues.append(f"{name}: {result['error']}")
    return {
        "ok": not issues,
        "integration_count": len(diagnostics),
        "diagnostics": diagnostics,
        "issues": issues,
        "warnings": warnings,
    }


def summary() -> dict[str, Any]:
    current = status()
    diagnostics = doctor()
    return {
        "ok": current["ok"] and diagnostics["ok"],
        "status_ok": current["ok"],
        "doctor_ok": diagnostics["ok"],
        "integration_count": current["integration_count"],
        "source_ready": current["source_ready"],
        "issues": diagnostics["issues"],
        "warnings": diagnostics["warnings"],
        "integrations": {
            name: {
                "source_commit": info.get("source_commit"),
                "pinned_commit": info.get("pinned_commit"),
                "source_exists": info.get("source_exists"),
            }
            for name, info in current["integrations"].items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Hermes external runtime integrations")
    parser.add_argument("command", choices=["status", "doctor", "summary"], nargs="?", default="summary")
    args = parser.parse_args()

    result = {"status": status, "doctor": doctor, "summary": summary}[args.command]()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
