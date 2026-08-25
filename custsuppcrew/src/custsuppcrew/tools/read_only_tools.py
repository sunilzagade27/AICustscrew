"""Least-privilege read-only CrewAI tools. SAD §2 tool catalog."""

from __future__ import annotations

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from custsuppcrew.tools.stub_client import get_json


class QueryInput(BaseModel):
    query: str = Field(
        default="",
        description=(
            "Optional filter (pod, service, search text). "
            "Empty returns the synthetic fixture set. "
            "Use __none__ to request an empty result."
        ),
    )


class PlaybookInput(BaseModel):
    query: str = Field(
        default="runbook/rb-crashloop-configmap",
        description="Playbook record id to fetch.",
    )


class EscalationInput(BaseModel):
    query: str = Field(
        default="escalation/plat-sre-15m",
        description="Escalation record id to fetch.",
    )


class GetStubTool(BaseTool):
    name: str
    description: str
    args_schema: Type[BaseModel] = QueryInput
    env_name: str
    path: str

    def _run(self, query: str = "") -> str:
        return get_json(self.env_name, self.path, query)


def _tool(
    name: str,
    description: str,
    env_name: str,
    path: str,
    schema: Type[BaseModel] = QueryInput,
) -> GetStubTool:
    return GetStubTool(
        name=name,
        description=description,
        args_schema=schema,
        env_name=env_name,
        path=path,
    )


def kubernetes_tools() -> list[BaseTool]:
    env = "STUB_K8S_BASE_URL"
    return [
        _tool(
            "get_pod_status",
            "Read-only pod status from the stub Kubernetes API. Never apply or restart.",
            env,
            "/k8s/pods",
        ),
        _tool(
            "get_node_status",
            "Read-only node status from the stub Kubernetes API.",
            env,
            "/k8s/nodes",
        ),
        _tool(
            "get_deployment_status",
            "Read-only deployment status from the stub Kubernetes API.",
            env,
            "/k8s/deployments",
        ),
        _tool(
            "get_cluster_events",
            "Read-only cluster events from the stub Kubernetes API.",
            env,
            "/k8s/events",
        ),
    ]


def logs_tools() -> list[BaseTool]:
    env = "STUB_LOGS_BASE_URL"
    return [
        _tool(
            "search_logs",
            "Read-only application log search against the stub log API.",
            env,
            "/logs/search",
        ),
        _tool(
            "count_log_patterns",
            "Read-only log pattern counts against the stub log API.",
            env,
            "/logs/patterns",
        ),
    ]


def metrics_tools() -> list[BaseTool]:
    env = "STUB_METRICS_BASE_URL"
    return [
        _tool(
            "get_performance_metrics",
            "Read-only latency/saturation series from the stub metrics API.",
            env,
            "/metrics/performance",
        ),
        _tool(
            "get_error_metrics",
            "Read-only error-rate series from the stub metrics API.",
            env,
            "/metrics/errors",
        ),
        _tool(
            "get_availability_metrics",
            "Read-only availability series from the stub metrics API.",
            env,
            "/metrics/availability",
        ),
    ]


def runbooks_tools() -> list[BaseTool]:
    env = "STUB_RUNBOOKS_BASE_URL"
    return [
        _tool(
            "search_runbooks",
            "Read-only search of stub playbooks and escalation docs.",
            env,
            "/runbooks/search",
        ),
        _tool(
            "get_playbook",
            "Read-only playbook fetch. Recommendations are not executed.",
            env,
            "/runbooks/playbooks",
            PlaybookInput,
        ),
        _tool(
            "get_escalation_procedure",
            "Read-only escalation procedure fetch. Not executed.",
            env,
            "/runbooks/escalation",
            EscalationInput,
        ),
    ]


def expected_tool_names() -> dict[str, list[str]]:
    return {
        "kubernetes_specialist": [t.name for t in kubernetes_tools()],
        "logs_specialist": [t.name for t in logs_tools()],
        "metrics_specialist": [t.name for t in metrics_tools()],
        "runbooks_specialist": [t.name for t in runbooks_tools()],
        "supervisor": [],
    }


def mutating_name_fragments() -> tuple[str, ...]:
    return ("apply", "restart", "scale", "rollback", "delete", "patch")


def assert_tools_read_only(tools: list[BaseTool]) -> None:
    banned = mutating_name_fragments()
    for tool in tools:
        lowered = tool.name.lower()
        if any(part in lowered for part in banned):
            raise RuntimeError(f"mutating tool name is not allowed: {tool.name}")


def bind_specialist_tools() -> dict[str, list[BaseTool]]:
    bound = {
        "kubernetes_specialist": kubernetes_tools(),
        "logs_specialist": logs_tools(),
        "metrics_specialist": metrics_tools(),
        "runbooks_specialist": runbooks_tools(),
        "supervisor": [],
    }
    for tools in bound.values():
        assert_tools_read_only(tools)
    return bound


def validate_bound_tools(bound: dict[str, list[BaseTool]]) -> None:
    expected = expected_tool_names()
    for agent_key, names in expected.items():
        actual = [tool.name for tool in bound.get(agent_key, [])]
        if actual != names:
            raise RuntimeError(
                f"tool bind mismatch for {agent_key}: {actual} != {names}"
            )
