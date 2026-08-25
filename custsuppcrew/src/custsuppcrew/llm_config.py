"""LLM model/temperature policy. SAD AD-10: low temperature when the model allows it."""

from __future__ import annotations

import os

from crewai import LLM

DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
DEFAULT_TEMPERATURE = 0.1
_NO_TEMPERATURE = ("gpt-5", "o1-", "o1/", "/o1", "o3-", "o3/", "/o3", "o4-")


def normalize_model(model: str) -> str:
    name = (model or DEFAULT_MODEL).strip()
    if "/" in name:
        return name
    if name.startswith(("gpt-", "o1", "o3", "o4")):
        return f"openai/{name}"
    return name


def supports_temperature(model: str) -> bool:
    lowered = normalize_model(model).lower()
    return not any(token in lowered for token in _NO_TEMPERATURE)


def investigation_llm() -> LLM:
    model = normalize_model(os.environ.get("MODEL", DEFAULT_MODEL))
    options: dict[str, object] = {"model": model}
    if supports_temperature(model):
        raw = os.environ.get("LLM_TEMPERATURE", str(DEFAULT_TEMPERATURE))
        options["temperature"] = float(raw)
    return LLM(**options)
