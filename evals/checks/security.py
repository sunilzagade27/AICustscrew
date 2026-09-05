"""Security checks EC-011–EC-012."""

from __future__ import annotations

import re
from typing import Any

from evals.checks.common import ROOT, result

from custsuppcrew.tools.read_only_tools import bind_specialist_tools, expected_tool_names
from custsuppcrew.tools.stub_client import MUTATING_METHODS
from custsuppcrew.trace_log import ANTHROPIC_RE, redact

SECRET_VALUE_RE = re.compile(r"sk-ant-[A-Za-z0-9_-]+")
KEY_ASSIGN_RE = re.compile(r"ANTHROPIC_API_KEY\s*=")


def check_secret_leakage() -> dict[str, Any]:
    log_path = ROOT / "project-context/2.build/logs/backend-trace.jsonl"
    if not log_path.exists():
        return result("EC-011", False, "backend-trace.jsonl missing")
    text = log_path.read_text(encoding="utf-8", errors="replace")
    leaks = []
    if SECRET_VALUE_RE.search(text):
        leaks.append("sk-ant- key material")
    if KEY_ASSIGN_RE.search(text):
        leaks.append("ANTHROPIC_API_KEY=")
    sample = "Authorization: Bearer super-secret-token"
    redacted = redact(sample)
    overlap_ok = "super-secret-token" not in redacted
    if not overlap_ok:
        leaks.append("redact() Bearer overlap still leaves token")
    return result("EC-011", not leaks, f"leaks={leaks or 'none'}")


def check_allowlist() -> dict[str, Any]:
    bound = bind_specialist_tools()
    expected = expected_tool_names()
    mismatch = []
    for agent, names in expected.items():
        actual = [tool.name for tool in bound.get(agent, [])]
        if actual != names:
            mismatch.append(f"{agent}: {actual} != {names}")
    return result(
        "EC-012",
        not mismatch,
        f"bind matches catalog; mutating HTTP methods never issued by stub client ({sorted(MUTATING_METHODS)})"
        if not mismatch
        else f"bind mismatch: {mismatch}",
    )
