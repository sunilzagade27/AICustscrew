"""Read-only stub OpenAPI surfaces. No mutating routes. SAD AD-07."""

from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from custsuppcrew.stubs import data

app = FastAPI(title="SRE stub telemetry", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "stub_data": "true"}


def _ok(tool: str, records: list[dict]) -> JSONResponse:
    return JSONResponse(data.envelope(tool, records))


@app.get("/k8s/pods")
def get_pods(query: str = Query(default="")) -> JSONResponse:
    return _ok("get_pod_status", data.filter_records(data.PODS, query))


@app.get("/k8s/nodes")
def get_nodes(query: str = Query(default="")) -> JSONResponse:
    return _ok("get_node_status", data.filter_records(data.NODES, query))


@app.get("/k8s/deployments")
def get_deployments(query: str = Query(default="")) -> JSONResponse:
    return _ok(
        "get_deployment_status",
        data.filter_records(data.DEPLOYMENTS, query),
    )


@app.get("/k8s/events")
def get_events(query: str = Query(default="")) -> JSONResponse:
    return _ok("get_cluster_events", data.filter_records(data.EVENTS, query))


@app.get("/logs/search")
def search_logs(query: str = Query(default="")) -> JSONResponse:
    return _ok("search_logs", data.filter_records(data.LOG_HITS, query))


@app.get("/logs/patterns")
def count_patterns(query: str = Query(default="")) -> JSONResponse:
    return _ok("count_log_patterns", data.filter_records(data.LOG_PATTERNS, query))


@app.get("/metrics/performance")
def get_performance(query: str = Query(default="")) -> JSONResponse:
    return _ok(
        "get_performance_metrics",
        data.filter_records(data.PERFORMANCE, query),
    )


@app.get("/metrics/errors")
def get_errors(query: str = Query(default="")) -> JSONResponse:
    return _ok("get_error_metrics", data.filter_records(data.ERRORS, query))


@app.get("/metrics/availability")
def get_availability(query: str = Query(default="")) -> JSONResponse:
    return _ok(
        "get_availability_metrics",
        data.filter_records(data.AVAILABILITY, query),
    )


@app.get("/runbooks/search")
def search_runbooks(query: str = Query(default="")) -> JSONResponse:
    combined = data.PLAYBOOKS + data.ESCALATION
    return _ok("search_runbooks", data.filter_records(combined, query))


@app.get("/runbooks/playbooks")
def get_playbook(query: str = Query(default="")) -> JSONResponse:
    if query in ("__none__", "__empty__"):
        return _ok("get_playbook", [])
    records = data.filter_records(data.PLAYBOOKS, query)
    return _ok("get_playbook", records)


@app.get("/runbooks/escalation")
def get_escalation(query: str = Query(default="")) -> JSONResponse:
    if query in ("__none__", "__empty__"):
        return _ok("get_escalation_procedure", [])
    records = data.filter_records(data.ESCALATION, query)
    return _ok("get_escalation_procedure", records)


def run_stubs() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8081)


if __name__ == "__main__":
    run_stubs()
