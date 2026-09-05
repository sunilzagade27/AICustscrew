"""Shared helpers for SAD §9 eval checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "custsuppcrew" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from custsuppcrew.stubs import data as stub_data  # noqa: E402

SPECIALISTS = (
    "kubernetes_specialist",
    "logs_specialist",
    "metrics_specialist",
    "runbooks_specialist",
)
REPORT_KEYS = (
    "key_insights",
    "next_steps",
    "critical_alerts",
    "troubleshooting_steps",
)
PLAN_S_MAX = 30.0
COMPLETE_S_MAX = 600.0
MAX_ITER_CAP = 12
EMPTY_TOOL_MARKERS = ("no data from", "returned no data", "empty_tools")


def allowed_fixture_ids() -> set[str]:
    catalogs = (
        stub_data.PODS,
        stub_data.NODES,
        stub_data.DEPLOYMENTS,
        stub_data.EVENTS,
        stub_data.LOG_HITS,
        stub_data.LOG_PATTERNS,
        stub_data.PERFORMANCE,
        stub_data.ERRORS,
        stub_data.AVAILABILITY,
        stub_data.PLAYBOOKS,
        stub_data.ESCALATION,
    )
    ids: set[str] = set()
    for rows in catalogs:
        for row in rows:
            if row.get("id"):
                ids.add(str(row["id"]))
            if row.get("name"):
                ids.add(str(row["name"]))
            if row.get("missing_configmap"):
                ids.add(str(row["missing_configmap"]))
    return ids


def numeric_fixture_points() -> set[float]:
    return {
        float(stub_data.PERFORMANCE[0]["baseline_ms"]),
        float(stub_data.PERFORMANCE[0]["current_ms"]),
        float(stub_data.PERFORMANCE[0]["ratio"]),
        float(stub_data.ERRORS[0]["error_rate"]),
        float(stub_data.AVAILABILITY[0]["availability"]),
        float(stub_data.PODS[0]["restarts"]),
        float(stub_data.LOG_HITS[0]["count"]),
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def insights(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    report = snapshot.get("report") or {}
    if isinstance(report, dict):
        for item in report.get("key_insights") or []:
            if isinstance(item, dict):
                rows.append(item)
    for specialist in snapshot.get("specialist_results") or []:
        if not isinstance(specialist, dict):
            continue
        for item in specialist.get("insights") or []:
            if isinstance(item, dict):
                rows.append(item)
    return rows


def state_asserting(item: dict[str, Any]) -> bool:
    text = str(item.get("text") or item.get("insight") or "").lower()
    if any(marker in text for marker in EMPTY_TOOL_MARKERS):
        return False
    return bool(text or item.get("source"))


def result(ec_id: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": ec_id, "pass": passed, "detail": detail}
