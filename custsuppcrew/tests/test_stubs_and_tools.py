from fastapi.testclient import TestClient

from custsuppcrew.stubs.app import app
from custsuppcrew.tools.read_only_tools import (
    bind_specialist_tools,
    mutating_name_fragments,
    validate_bound_tools,
)
from custsuppcrew.tools.stub_client import MUTATING_METHODS, assert_not_mutating


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_pods_fixture_has_source_id() -> None:
    response = client.get("/k8s/pods")
    body = response.json()
    assert response.status_code == 200
    assert body["stub_data"] is True
    assert body["tool"] == "get_pod_status"
    assert body["records"][0]["id"]
    assert "CrashLoopBackOff" in body["records"][0]["status"]


def test_empty_tool_result() -> None:
    response = client.get("/logs/search", params={"query": "__none__"})
    body = response.json()
    assert body["records"] == []


def test_mutating_http_rejected() -> None:
    response = client.post("/k8s/pods")
    assert response.status_code == 405


def test_tools_bind_read_only() -> None:
    bound = bind_specialist_tools()
    validate_bound_tools(bound)
    names = " ".join(tool.name for tools in bound.values() for tool in tools)
    for fragment in mutating_name_fragments():
        assert fragment not in names
    assert bound["supervisor"] == []
    assert "get_pod_status" in [tool.name for tool in bound["kubernetes_specialist"]]


def test_assert_not_mutating() -> None:
    for method in MUTATING_METHODS:
        try:
            assert_not_mutating(method)
            raise AssertionError(f"{method} should be rejected")
        except ValueError:
            pass
    assert_not_mutating("GET")
