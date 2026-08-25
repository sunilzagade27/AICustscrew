import time
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from custsuppcrew import investigation as investigation_mod
from custsuppcrew.api import app
from custsuppcrew.investigation import FLIGHT, CrewRunError, run_kickoff
from custsuppcrew.llm_config import normalize_model, supports_temperature


client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_flight() -> None:
    FLIGHT.release()
    yield
    FLIGHT.release()


def test_health_no_llm() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_empty_symptom_rejected_without_accept_header() -> None:
    response = client.post("/v1/investigations", json={"symptom": "   "})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert FLIGHT.busy() is False


def test_empty_string_symptom_rejected() -> None:
    response = client.post("/v1/investigations", json={"symptom": ""})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_symptom_rejected() -> None:
    response = client.post("/v1/investigations", json={})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_investigation() -> None:
    response = client.get("/v1/investigations/does-not-exist")
    assert response.status_code == 404


def test_busy_returns_429() -> None:
    assert FLIGHT.try_acquire() is True
    try:
        response = client.post(
            "/v1/investigations",
            json={"symptom": "pods crash looping"},
            headers={"accept": "application/json"},
        )
        assert response.status_code == 429
        assert response.json()["error"]["code"] == "BUSY"
    finally:
        FLIGHT.release()


def test_kickoff_cap_returns_crew_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(investigation_mod, "MAX_EXECUTION_SECONDS", 0.05)

    class FakeCrew:
        def kickoff(self, inputs: dict | None = None) -> SimpleNamespace:
            time.sleep(1)
            return SimpleNamespace(tasks_output=[])

    class FakeWrapper:
        def crew(self) -> FakeCrew:
            return FakeCrew()

    monkeypatch.setattr(investigation_mod, "Custsuppcrew", FakeWrapper)
    with pytest.raises(CrewRunError) as err:
        run_kickoff("api latency 3x")
    assert err.value.code == "CREW_TIMEOUT"


def test_temperature_policy() -> None:
    assert supports_temperature("anthropic/claude-sonnet-4-20250514") is True
    assert supports_temperature("gpt-5.5") is False
    assert normalize_model("gpt-5.5") == "openai/gpt-5.5"
    assert normalize_model("anthropic/claude-sonnet-4-20250514").startswith("anthropic/")
