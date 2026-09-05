"""Synthetic stub telemetry for MVP QA (not customer truth). AC-008."""

from __future__ import annotations

STUB_DISCLAIMER = (
    "stub_data=true; synthetic fixture for local MVP; not production telemetry"
)

PODS = [
    {
        "id": "pod/payments-api-7f9c-abc",
        "name": "payments-api-7f9c-abc",
        "namespace": "demo",
        "status": "CrashLoopBackOff",
        "reason": "Missing ConfigMap payments-api-config",
        "restarts": 12,
    }
]

NODES = [
    {
        "id": "node/demo-worker-1",
        "name": "demo-worker-1",
        "ready": True,
        "cpu_pressure": False,
    }
]

DEPLOYMENTS = [
    {
        "id": "deploy/payments-api",
        "name": "payments-api",
        "namespace": "demo",
        "replicas_desired": 2,
        "replicas_ready": 0,
        "missing_configmap": "payments-api-config",
    }
]

EVENTS = [
    {
        "id": "event/cfgmap-missing-1",
        "object": "pod/payments-api-7f9c-abc",
        "type": "Warning",
        "reason": "FailedMount",
        "message": "ConfigMap payments-api-config not found (synthetic fixture)",
    }
]

LOG_HITS = [
    {
        "id": "log/log-4421",
        "timestamp": "2026-08-24T18:00:00Z",
        "severity": "ERROR",
        "message": "configmap \"payments-api-config\" not found (synthetic fixture)",
        "count": 84,
    }
]

LOG_PATTERNS = [
    {
        "id": "pattern/crashloop",
        "pattern": "CrashLoopBackOff",
        "count": 12,
    },
    {
        "id": "pattern/configmap-missing",
        "pattern": "ConfigMap not found",
        "count": 84,
    },
]

PERFORMANCE = [
    {
        "id": "metric/p99-latency-1h",
        "service": "payments-api",
        "window": "1h",
        "baseline_ms": 150,
        "current_ms": 450,
        "ratio": 3.0,
        "note": "3x p99 vs baseline (synthetic fixture)",
    }
]

ERRORS = [
    {
        "id": "metric/error-rate-1h",
        "service": "payments-api",
        "window": "1h",
        "error_rate": 0.18,
        "note": "elevated 5xx (synthetic fixture)",
    }
]

AVAILABILITY = [
    {
        "id": "metric/availability-1h",
        "service": "payments-api",
        "window": "1h",
        "availability": 0.82,
        "note": "ready replicas 0/2 (synthetic fixture)",
    }
]

PLAYBOOKS = [
    {
        "id": "runbook/rb-crashloop-configmap",
        "title": "CrashLoopBackOff with missing ConfigMap",
        "section": "3. Verify ConfigMap exists before rolling pods",
        "steps": [
            "Read ConfigMap payments-api-config in the workload namespace",
            "Compare deployment volume/envFrom references",
            "Do not restart or apply manifests from the assistant",
        ],
        "executed": False,
    }
]

ESCALATION = [
    {
        "id": "escalation/plat-sre-15m",
        "title": "Platform SRE escalation",
        "section": "Page platform on-call if ConfigMap missing > 15 minutes",
        "executed": False,
    }
]


def envelope(tool: str, records: list[dict]) -> dict:
    return {
        "tool": tool,
        "records": records,
        "stub_data": True,
        "disclaimer": STUB_DISCLAIMER,
    }


def filter_records(records: list[dict], query: str) -> list[dict]:
    q = (query or "").strip()
    if q in ("__none__", "__empty__"):
        return []
    if not q:
        return records
    lowered = q.lower()
    return [
        row
        for row in records
        if lowered in json_blob(row).lower()
    ]


def json_blob(row: dict) -> str:
    return " ".join(str(v) for v in row.values())
