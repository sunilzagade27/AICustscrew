#!/usr/bin/env python3
"""Offline-first eval runner for SAD §9 EC-001–EC-013.

Usage (from repo root):
  PYTHONPATH=. python evals/run.py
  PYTHONPATH=. python evals/run.py --live   # optional; one fixture POST if API is up
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "custsuppcrew" / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

from evals.checks.accuracy import (  # noqa: E402
    check_banned_absent_from_catalog,
    check_hallucinated_objects,
    check_numeric_grounding,
    check_report_schema,
    check_source_ids,
    check_specialist_attribution,
)
from evals.checks.common import load_json  # noqa: E402
from evals.checks.cost import check_tokens_logged  # noqa: E402
from evals.checks.latency import check_caps_in_code, check_completion, check_time_to_plan  # noqa: E402
from evals.checks.safety import (  # noqa: E402
    check_empty_tool_honesty,
    check_mutating_tools,
    check_unexecuted_remediation,
)
from evals.checks.security import check_allowlist, check_secret_leakage  # noqa: E402

SNAPSHOT_CHECKS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "EC-001": check_source_ids,
    "EC-002": check_hallucinated_objects,
    "EC-003": check_numeric_grounding,
    "EC-004": check_report_schema,
    "EC-005": check_specialist_attribution,
    "EC-006": check_time_to_plan,
    "EC-007": check_completion,
    "EC-009": check_unexecuted_remediation,
    "EC-010": check_empty_tool_honesty,
}

STATIC_CHECKS: dict[str, Callable[[], dict[str, Any]]] = {
    "EC-008": check_mutating_tools,
    "EC-011": check_secret_leakage,
    "EC-012": check_allowlist,
    "EC-013": check_tokens_logged,
}


def dataset_files() -> list[Path]:
    return sorted((ROOT / "evals" / "dataset").glob("*.jsonl"))


def load_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in dataset_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(json.loads(line))
    return items


def load_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    rel = item.get("recorded_path")
    if not rel:
        return {}
    snapshot = load_json(ROOT / rel)
    if item.get("banned_object_ids"):
        snapshot = {**snapshot, "banned_object_ids": item["banned_object_ids"]}
    return snapshot


def grade_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mode = item.get("mode")
    if mode == "api":
        rows.append(_grade_api(item))
        return rows
    snapshot = load_snapshot(item) if mode == "recorded" else {}
    for ec_id in item.get("checks") or []:
        if mode == "static" and ec_id == "EC-002":
            graded = check_banned_absent_from_catalog(item.get("banned_object_ids") or [])
        elif mode == "static" and ec_id == "EC-009":
            graded = check_unexecuted_remediation()
        elif mode == "static" and ec_id == "EC-010":
            graded = check_empty_tool_honesty()
        elif ec_id in STATIC_CHECKS and mode == "static":
            graded = STATIC_CHECKS[ec_id]()
        elif ec_id in SNAPSHOT_CHECKS and snapshot:
            graded = SNAPSHOT_CHECKS[ec_id](snapshot)
        elif ec_id in STATIC_CHECKS:
            graded = STATIC_CHECKS[ec_id]()
        else:
            graded = {"id": ec_id, "pass": False, "detail": f"no grader for {ec_id} in mode {mode}"}
        rows.append({**graded, "item": item["id"], "category": item["category"]})
    return rows


def _grade_api(item: dict[str, Any]) -> dict[str, Any]:
    from fastapi.testclient import TestClient

    from custsuppcrew.api import app

    client = TestClient(app)
    response = client.post("/v1/investigations", json={"symptom": item.get("symptom", "")})
    body = response.json()
    code = (body.get("error") or {}).get("code")
    ok = response.status_code == item.get("expect_http") and code == item.get("expect_code")
    return {
        "id": "AC-002",
        "pass": ok,
        "detail": f"HTTP {response.status_code} code={code}",
        "item": item["id"],
        "category": item["category"],
    }


def maybe_live(base_url: str) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=2) as resp:
            health = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ran": False, "detail": f"API not reachable: {exc}"}
    return {"ran": False, "detail": f"API up ({health}); live fixture POST skipped (≈5 min / item)"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for item in load_items():
        rows.extend(grade_item(item))
    rows.append({**check_caps_in_code(), "item": "STATIC-CAPS", "category": "static_caps"})

    by_ec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_ec[row["id"]].append(row)
        by_cat[row["category"]].append(row)

    live = maybe_live(args.api_url) if args.live else {"ran": False, "detail": "offline mode"}
    summary = {
        "rows": rows,
        "by_ec": {
            ec: {"pass": all(r["pass"] for r in items), "n": len(items), "fails": [r for r in items if not r["pass"]]}
            for ec, items in sorted(by_ec.items())
        },
        "by_category": {
            cat: {"pass": all(r["pass"] for r in items), "n": len(items)}
            for cat, items in sorted(by_cat.items())
        },
        "live": live,
    }
    out = ROOT / "evals" / "results.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"by_ec": summary["by_ec"], "by_category": summary["by_category"], "live": live}, indent=2))
    required = [ec for ec in summary["by_ec"] if ec.startswith("EC-")]
    failed = [ec for ec in required if not summary["by_ec"][ec]["pass"]]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
