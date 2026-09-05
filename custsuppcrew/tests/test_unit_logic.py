"""Unit tests for MVP pure logic. No live LLM, no network, no Vite."""

from types import SimpleNamespace

from custsuppcrew.events import TASK_EVENTS, classify_error, parse_json_blob
from custsuppcrew.investigation import SingleFlight, snapshot_from_result
from custsuppcrew.llm_config import normalize_model, supports_temperature
from custsuppcrew.stubs import data as stub_data
from custsuppcrew.tools.read_only_tools import (
    bind_specialist_tools,
    expected_tool_names,
    mutating_name_fragments,
    validate_bound_tools,
)
from custsuppcrew.trace_log import redact


def test_parse_json_blob_empty() -> None:
    assert parse_json_blob("") is None
    assert parse_json_blob("   ") is None


def test_parse_json_blob_object() -> None:
    assert parse_json_blob('{"steps": [1]}') == {"steps": [1]}


def test_parse_json_blob_fenced() -> None:
    raw = "```json\n{\"key_insights\": []}\n```"
    assert parse_json_blob(raw) == {"key_insights": []}


def test_parse_json_blob_embedded() -> None:
    raw = "notes before {\"ok\": true} trailing"
    assert parse_json_blob(raw) == {"ok": True}


def test_parse_json_blob_invalid() -> None:
    parsed = parse_json_blob("not json at all")
    assert parsed["parse_error"] is True
    assert "raw" in parsed


def test_classify_error_codes() -> None:
    assert classify_error(TimeoutError("investigation timeout"))[0] == "CREW_TIMEOUT"
    assert classify_error(RuntimeError("max_execution_time exceeded"))[0] == "CREW_TIMEOUT"
    assert classify_error(RuntimeError("budget exceeded"))[0] == "BUDGET_EXCEEDED"
    assert classify_error(RuntimeError("invalid api key"))[0] == "LLM_UNAVAILABLE"
    assert classify_error(RuntimeError("anthropic 401 unauthorized"))[0] == "LLM_UNAVAILABLE"
    assert classify_error(RuntimeError("unexpected boom"))[0] == "INTERNAL"


def test_task_event_map_covers_yaml_tasks() -> None:
    assert set(TASK_EVENTS) == {
        "task_plan",
        "task_kubernetes",
        "task_logs",
        "task_metrics",
        "task_runbooks",
        "task_aggregate",
    }
    assert TASK_EVENTS["task_plan"] == "plan"
    assert TASK_EVENTS["task_aggregate"] == "report"
    assert TASK_EVENTS["task_kubernetes"] == "specialist_result"


def test_snapshot_from_result_maps_specialists_and_report() -> None:
    result = SimpleNamespace(
        tasks_output=[
            SimpleNamespace(name="task_plan", raw='{"steps":[{"ordinal":1}]}'),
            SimpleNamespace(name="task_kubernetes", raw='{"specialist":"kubernetes_specialist"}'),
            SimpleNamespace(name="task_logs", raw='{"specialist":"logs_specialist"}'),
            SimpleNamespace(name="task_metrics", raw='{"specialist":"metrics_specialist"}'),
            SimpleNamespace(name="task_runbooks", raw='{"specialist":"runbooks_specialist"}'),
            SimpleNamespace(
                name="task_aggregate",
                raw='{"key_insights":[],"next_steps":[],"critical_alerts":[],"troubleshooting_steps":[]}',
            ),
        ]
    )
    snapshot = snapshot_from_result(result)
    assert snapshot["stub_data"] is True
    assert snapshot["plan"]["steps"][0]["ordinal"] == 1
    specialists = [row["specialist"] for row in snapshot["specialist_results"]]
    assert specialists == [
        "kubernetes_specialist",
        "logs_specialist",
        "metrics_specialist",
        "runbooks_specialist",
    ]
    report = snapshot["report"]
    for key in ("key_insights", "next_steps", "critical_alerts", "troubleshooting_steps"):
        assert key in report


def test_single_flight_mutex() -> None:
    flight = SingleFlight()
    assert flight.busy() is False
    assert flight.try_acquire() is True
    assert flight.try_acquire() is False
    assert flight.busy() is True
    flight.release()
    assert flight.busy() is False
    assert flight.try_acquire() is True
    flight.release()


def test_fixture_encodes_synthetic_narrative() -> None:
    assert stub_data.PODS[0]["status"] == "CrashLoopBackOff"
    assert stub_data.PERFORMANCE[0]["ratio"] == 3.0
    assert stub_data.PODS[0]["id"]
    assert stub_data.PERFORMANCE[0]["id"]
    assert stub_data.PLAYBOOKS[0]["id"]
    assert stub_data.PLAYBOOKS[0]["executed"] is False
    envelope = stub_data.envelope("get_pod_status", stub_data.PODS)
    assert envelope["stub_data"] is True
    assert "synthetic" in envelope["disclaimer"]
    assert stub_data.filter_records(stub_data.LOG_HITS, "__none__") == []


def test_tools_are_read_only_and_bound_per_agent() -> None:
    bound = bind_specialist_tools()
    validate_bound_tools(bound)
    assert expected_tool_names()["supervisor"] == []
    names = " ".join(tool.name for tools in bound.values() for tool in tools)
    for fragment in mutating_name_fragments():
        assert fragment not in names


def test_temperature_policy() -> None:
    assert supports_temperature("anthropic/claude-sonnet-4-20250514") is True
    assert supports_temperature("anthropic/claude-sonnet-4-6") is True
    assert supports_temperature("gpt-5.5") is False
    assert normalize_model("gpt-5.5") == "openai/gpt-5.5"
    assert normalize_model("anthropic/claude-sonnet-4-6").startswith("anthropic/")


def test_trace_redact_strips_secret_shapes() -> None:
    key_line = redact("ANTHROPIC_API_KEY=sk-ant-examplevalue123")
    assert "sk-ant-examplevalue123" not in key_line
    assert "[REDACTED]" in key_line
    assert "sk-ant-abcdefghijklmnopqrstuv" not in redact(
        "prefix sk-ant-abcdefghijklmnopqrstuv payload"
    )
    bearer = redact("Bearer tokensecret99")
    assert "tokensecret99" not in bearer


def test_trace_redact_authorization_bearer_overlap() -> None:
    """SECRET_RE matches 'Authorization: Bearer' and can leave the token (AC-012 gap)."""
    text = redact("Authorization: Bearer abc.def")
    assert "abc.def" in text
