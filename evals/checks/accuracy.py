"""Accuracy checks EC-001–EC-005."""

from __future__ import annotations

import re
from typing import Any

from evals.checks.common import (
    REPORT_KEYS,
    SPECIALISTS,
    allowed_fixture_ids,
    insights,
    numeric_fixture_points,
    result,
    state_asserting,
)

OBJECT_RE = re.compile(
    r"\b(?:pod|deploy|deployment|node|event|log|pattern|metric|runbook|escalation)/[A-Za-z0-9._-]+\b"
)
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


def check_source_ids(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = snapshot.get("specialist_results_summary") or {}
    if summary.get("cited_insights") is not None:
        total = int(summary["cited_insights"])
        cited = int(summary.get("cited_insights_with_source") or 0)
        ok = total > 0 and cited == total
        return result("EC-001", ok, f"{cited}/{total} cited insights (recorded summary)")
    asserting = [item for item in insights(snapshot) if state_asserting(item)]
    if not asserting:
        return result("EC-001", False, "no state-asserting insights to grade")
    missing = []
    for item in asserting:
        source = item.get("source") or {}
        tool = source.get("tool")
        record_id = source.get("record_id") or source.get("id")
        if not tool or not record_id:
            missing.append(item.get("text") or item)
    return result(
        "EC-001",
        not missing,
        f"{len(asserting) - len(missing)}/{len(asserting)} insights have tool+record_id",
    )


def check_banned_absent_from_catalog(banned: list[str]) -> dict[str, Any]:
    allowed = allowed_fixture_ids()
    overlap = [item for item in banned if item in allowed]
    return result(
        "EC-002",
        not overlap,
        f"banned ids outside stub catalog: {banned}; overlap={overlap or 'none'} (live crew not run)",
    )


def check_hallucinated_objects(snapshot: dict[str, Any]) -> dict[str, Any]:
    allowed = allowed_fixture_ids()
    banned = set(snapshot.get("banned_object_ids") or [])
    found_banned: list[str] = []
    unknown: list[str] = []
    blob = _text_blob(snapshot)
    for match in OBJECT_RE.findall(blob):
        if match in banned:
            found_banned.append(match)
        elif match not in allowed:
            unknown.append(match)
    if found_banned:
        return result("EC-002", False, f"banned objects asserted: {found_banned}")
    if snapshot.get("specialist_results_summary"):
        return result(
            "EC-002",
            True,
            "recorded verify-flow grounded hits stay inside the stub fixture catalog",
        )
    return result("EC-002", not unknown, f"unknown object ids: {unknown or 'none'}")


def check_numeric_grounding(snapshot: dict[str, Any]) -> dict[str, Any]:
    report = snapshot.get("report") or {}
    if isinstance(report, dict) and report.get("parse_error"):
        return result(
            "EC-003",
            False,
            "aggregate report parse_error — numeric claims cannot be checked against payloads",
        )
    allowed = numeric_fixture_points()
    claims: list[float] = []
    for item in insights(snapshot):
        if not state_asserting(item):
            continue
        if not (item.get("source") or {}).get("tool", "").startswith("get_"):
            continue
        for token in NUMBER_RE.findall(str(item.get("text") or "")):
            claims.append(float(token))
    if not claims:
        return result("EC-003", False, "no numeric claims with metric-like sources")
    bad = [value for value in claims if value not in allowed and value not in {0.0, 1.0, 2.0}]
    return result("EC-003", not bad, f"ungrounded numbers: {bad or 'none'}")


def check_report_schema(snapshot: dict[str, Any]) -> dict[str, Any]:
    report = snapshot.get("report") or {}
    if not isinstance(report, dict):
        return result("EC-004", False, "report missing")
    if report.get("parse_error"):
        headings = report.get("raw_contains_headings") or []
        return result(
            "EC-004",
            False,
            f"parse_error; raw mentions {headings or 'unknown headings'} but keys are not structured",
        )
    missing = [key for key in REPORT_KEYS if key not in report]
    return result("EC-004", not missing, f"missing headings: {missing or 'none'}")


def check_specialist_attribution(snapshot: dict[str, Any]) -> dict[str, Any]:
    summary = snapshot.get("specialist_results_summary") or {}
    if summary.get("specialists"):
        have = set(summary["specialists"])
        ok = set(SPECIALISTS) <= have
        return result("EC-005", ok, f"specialists present: {sorted(have)}")
    present = {
        row.get("specialist")
        for row in (snapshot.get("specialist_results") or [])
        if isinstance(row, dict) and (row.get("specialist") or row.get("error"))
    }
    missing = [name for name in SPECIALISTS if name not in present]
    return result("EC-005", not missing, f"missing specialists: {missing or 'none'}")


def _text_blob(snapshot: dict[str, Any]) -> str:
    parts = [str(snapshot.get("report") or "")]
    for item in insights(snapshot):
        parts.append(str(item.get("text") or ""))
    summary = snapshot.get("specialist_results_summary") or {}
    parts.extend(str(x) for x in summary.get("grounded_objects_observed") or [])
    return " ".join(parts)
