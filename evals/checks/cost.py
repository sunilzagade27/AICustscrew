"""Cost check EC-013 — log presence only (operator: no spend ceiling)."""

from __future__ import annotations

import json
from typing import Any

from evals.checks.common import ROOT, result

USAGE_KEYS = ("input_tokens", "output_tokens", "total_tokens", "prompt_tokens", "completion_tokens")


def check_tokens_logged() -> dict[str, Any]:
    log_path = ROOT / "project-context/2.build/logs/backend-trace.jsonl"
    if not log_path.exists():
        return result("EC-013", False, "backend-trace.jsonl missing")
    found = 0
    completes = 0
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") != "kickoff_complete":
            continue
        completes += 1
        payload = row.get("payload") or {}
        usage = payload.get("usage") or payload
        if any(key in usage and usage.get(key) is not None for key in USAGE_KEYS):
            found += 1
    if completes == 0:
        return result(
            "EC-013",
            False,
            "no kickoff_complete traces yet; instrumentation now writes usage on the next live run",
        )
    return result(
        "EC-013",
        found > 0,
        f"{found}/{completes} kickoff_complete lines include token usage (no dollar ceiling)",
    )
