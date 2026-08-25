"""Parse crew task outputs into SAD investigation events."""

from __future__ import annotations

import json
import re
from typing import Any

TASK_EVENTS = {
    "task_plan": "plan",
    "task_kubernetes": "specialist_result",
    "task_logs": "specialist_result",
    "task_metrics": "specialist_result",
    "task_runbooks": "specialist_result",
    "task_aggregate": "report",
}

FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def parse_json_blob(raw: str) -> Any:
    text = (raw or "").strip()
    if not text:
        return None
    fenced = FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {"raw": raw, "parse_error": True}
        return {"raw": raw, "parse_error": True}


def classify_error(exc: BaseException) -> tuple[str, str]:
    message = str(exc)
    lowered = message.lower()
    if "timeout" in lowered or "max_execution_time" in lowered:
        return "CREW_TIMEOUT", message
    if "budget" in lowered or "max_iter" in lowered or "max rpm" in lowered:
        return "BUDGET_EXCEEDED", message
    if any(
        token in lowered
        for token in ("api key", "anthropic", "authentication", "unauthorized", "llm")
    ):
        return "LLM_UNAVAILABLE", message
    return "INTERNAL", message
