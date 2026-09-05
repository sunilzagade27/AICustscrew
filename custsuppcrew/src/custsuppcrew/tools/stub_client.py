"""Read-only HTTP GET client for stub OpenAPI tools."""

from __future__ import annotations

import json
import os

import httpx

DEFAULT_STUB_BASE = "http://127.0.0.1:8081"
TIMEOUT_SECONDS = 15.0
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def stub_base_url(env_name: str) -> str:
    return os.environ.get(env_name, DEFAULT_STUB_BASE).rstrip("/")


def get_json(env_name: str, path: str, query: str = "") -> str:
    """GET-only fetch. Never issues mutating HTTP methods."""
    url = f"{stub_base_url(env_name)}{path}"
    params = {"query": query} if query is not None else {}
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        payload = {
            "tool": path,
            "records": [],
            "stub_data": True,
            "error": "STUB_UNAVAILABLE",
            "message": str(exc),
        }
        return json.dumps(payload)


def assert_not_mutating(method: str) -> None:
    if method.upper() in MUTATING_METHODS:
        raise ValueError(f"mutating HTTP method is not allowed: {method}")
