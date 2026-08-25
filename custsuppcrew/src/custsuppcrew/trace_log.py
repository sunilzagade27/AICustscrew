"""Redacted investigation logs. AC-012."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+"
)
ANTHROPIC_RE = re.compile(r"sk-ant-[A-Za-z0-9_-]+")
BEARER_RE = re.compile(r"(?i)bearer\s+\S+")


def aamad_root() -> Path:
    return Path(__file__).resolve().parents[3]


def log_dir() -> Path:
    path = aamad_root() / "project-context" / "2.build" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def redact(text: str) -> str:
    redacted = SECRET_RE.sub(r"\1=[REDACTED]", text)
    redacted = ANTHROPIC_RE.sub("[REDACTED]", redacted)
    return BEARER_RE.sub("Bearer [REDACTED]", redacted)


def write_trace(event: str, payload: dict[str, Any]) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
    }
    line = redact(json.dumps(record, default=str))
    (log_dir() / "backend-trace.jsonl").open("a", encoding="utf-8").write(line + "\n")
