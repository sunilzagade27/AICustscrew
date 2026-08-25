"""Investigation chat API — SAD §4. Port 8000."""

from __future__ import annotations

import json
import queue
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from custsuppcrew.investigation import (
    FLIGHT,
    SENTINEL,
    CrewRunError,
    new_investigation_id,
    run_kickoff,
    start_background,
)

SYMPTOM_MAX = 8192
app = FastAPI(title="SRE investigation API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

_store: dict[str, dict[str, Any]] = {}


def error_body(code: str, message: str, diagnostic: str = "") -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "diagnostic": diagnostic or message,
        }
    }


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content=error_body(code, message))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _validate_symptom(raw: Any) -> tuple[str | None, JSONResponse | None]:
    if not isinstance(raw, str) or not raw.strip():
        return None, error_response(
            400, "VALIDATION_ERROR", "symptom is required and must be non-empty"
        )
    if len(raw) > SYMPTOM_MAX:
        return None, error_response(
            400, "VALIDATION_ERROR", f"symptom exceeds {SYMPTOM_MAX} characters"
        )
    return raw.strip(), None


def _want_json(request: Request, stream: bool | None) -> bool:
    if stream is False:
        return True
    if stream is True:
        return False
    accept = request.headers.get("accept", "")
    return "application/json" in accept and "text/event-stream" not in accept


@app.post("/v1/investigations", response_model=None)
async def create_investigation(
    request: Request,
    stream: bool | None = Query(default=None),
) -> JSONResponse | StreamingResponse:
    try:
        body = await request.json()
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "JSON body required")
    symptom, err = _validate_symptom(
        body.get("symptom") if isinstance(body, dict) else None
    )
    if err:
        return err
    assert symptom is not None
    if not FLIGHT.try_acquire():
        return error_response(
            429, "BUSY", "another investigation is already running"
        )

    investigation_id = new_investigation_id()
    _store[investigation_id] = {
        "investigation_id": investigation_id,
        "status": "running",
        "plan": None,
        "specialist_results": [],
        "report": None,
        "diagnostic": None,
        "stub_data": True,
    }

    try:
        if _want_json(request, stream):
            return _run_json(investigation_id, symptom)
        return StreamingResponse(
            _sse_generator(investigation_id, symptom),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception:
        FLIGHT.release()
        raise


def _run_json(investigation_id: str, symptom: str) -> JSONResponse:
    try:
        snapshot = run_kickoff(symptom, on_thread_done=FLIGHT.release)
        record = {**_store[investigation_id], **snapshot, "status": "complete"}
        _store[investigation_id] = record
        return JSONResponse(record)
    except CrewRunError as exc:
        record = {
            **_store[investigation_id],
            "status": "failed",
            "diagnostic": error_body(exc.code, exc.message),
        }
        _store[investigation_id] = record
        return JSONResponse(status_code=502, content=error_body(exc.code, exc.message))


def _sse_generator(investigation_id: str, symptom: str):
    event_q: queue.Queue[Any] = queue.Queue()

    def _on_done(snapshot: dict[str, Any] | None, error: CrewRunError | None) -> None:
        current = _store.get(investigation_id, {})
        if snapshot is not None:
            _store[investigation_id] = {**current, **snapshot, "status": "complete"}
        elif error is not None:
            _store[investigation_id] = {
                **current,
                "status": "failed",
                "diagnostic": error_body(error.code, error.message),
            }

    start_background(
        symptom,
        event_q,
        _on_done,
        on_thread_done=FLIGHT.release,
    )
    yield _sse(
        "started",
        {"investigation_id": investigation_id, "stub_data": True},
    )
    while True:
        item = event_q.get()
        if item is SENTINEL:
            break
        yield _sse(item.get("event", "diagnostic"), item.get("data"))


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@app.get("/v1/investigations/{investigation_id}")
def get_investigation(investigation_id: str) -> JSONResponse:
    record = _store.get(investigation_id)
    if record is None:
        return error_response(404, "INTERNAL", "investigation not found")
    return JSONResponse(record)


def run_api() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run_api()
