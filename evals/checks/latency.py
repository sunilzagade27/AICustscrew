"""Latency checks EC-006–EC-007."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evals.checks.common import COMPLETE_S_MAX, MAX_ITER_CAP, PLAN_S_MAX, ROOT, result


def check_time_to_plan(snapshot: dict[str, Any]) -> dict[str, Any]:
    latency = snapshot.get("latency") or {}
    plan_s = latency.get("plan_s")
    if plan_s is None:
        return result("EC-006", False, "no plan latency recorded")
    return result(
        "EC-006",
        float(plan_s) <= PLAN_S_MAX,
        f"plan at {plan_s}s (gate ≤ {PLAN_S_MAX}s max, not p95)",
    )


def check_completion(snapshot: dict[str, Any]) -> dict[str, Any]:
    latency = snapshot.get("latency") or {}
    complete_s = latency.get("complete_s")
    if complete_s is None:
        return result("EC-007", False, "no completion latency recorded")
    over_iter = latency.get("max_iter_exceeded")
    ok = float(complete_s) <= COMPLETE_S_MAX and over_iter is not True
    return result(
        "EC-007",
        ok,
        f"complete at {complete_s}s (gate ≤ {COMPLETE_S_MAX}s); max_iter exceeded={over_iter}",
    )


def check_caps_in_code() -> dict[str, Any]:
    investigation = (ROOT / "custsuppcrew/src/custsuppcrew/investigation.py").read_text(
        encoding="utf-8"
    )
    agents = (ROOT / "custsuppcrew/src/custsuppcrew/config/agents.yaml").read_text(
        encoding="utf-8"
    )
    has_600 = "MAX_EXECUTION_SECONDS = 600" in investigation
    has_iter = f"max_iter: {MAX_ITER_CAP}" in agents
    return result(
        "EC-007-caps",
        has_600 and has_iter,
        f"code caps present: 600s={has_600}, max_iter {MAX_ITER_CAP}={has_iter}",
    )


def agents_yaml() -> Path:
    return ROOT / "custsuppcrew/src/custsuppcrew/config/agents.yaml"
