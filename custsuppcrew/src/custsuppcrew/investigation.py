"""Run the sequential crew and map task outputs to SAD events."""

from __future__ import annotations

import queue
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Callable
from uuid import uuid4

from custsuppcrew.crew import Custsuppcrew
from custsuppcrew.events import TASK_EVENTS, classify_error, parse_json_blob
from custsuppcrew.trace_log import write_trace

MAX_EXECUTION_SECONDS = 600
SENTINEL = object()


class SingleFlight:
    """One investigation per process. Release only when kickoff thread finishes."""

    def __init__(self) -> None:
        self._busy = False
        self._guard = threading.Lock()

    def try_acquire(self) -> bool:
        with self._guard:
            if self._busy:
                return False
            self._busy = True
            return True

    def release(self) -> None:
        with self._guard:
            self._busy = False

    def busy(self) -> bool:
        with self._guard:
            return self._busy


FLIGHT = SingleFlight()


def _usage_fields(result: Any) -> dict[str, Any] | None:
    """Normalize CrewAI token usage for EC-013 traces (names only, no secrets)."""
    usage = getattr(result, "token_usage", None)
    if usage is None:
        return None
    if isinstance(usage, dict):
        payload = usage
    else:
        payload = {
            "input_tokens": getattr(usage, "prompt_tokens", None)
            or getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "completion_tokens", None)
            or getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        }
    return {key: value for key, value in payload.items() if value is not None} or None


def new_investigation_id() -> str:
    return str(uuid4())


def _attach_callbacks(crew: Any, event_q: queue.Queue[Any]) -> None:
    for task in crew.tasks:
        event_name = TASK_EVENTS.get(task.name or "")
        if not event_name:
            continue

        def _callback(output: Any, name: str = event_name, task_name: str = task.name) -> None:
            payload = parse_json_blob(getattr(output, "raw", str(output)))
            event_q.put({"event": name, "task": task_name, "data": payload})
            write_trace(
                "task_complete",
                {"task": task_name, "event": name, "agent": getattr(output, "agent", "")},
            )

        task.callback = _callback


def snapshot_from_result(result: Any) -> dict[str, Any]:
    plan = None
    specialist_results: list[Any] = []
    report = None
    outputs = getattr(result, "tasks_output", []) or []
    for output in outputs:
        name = getattr(output, "name", "") or ""
        parsed = parse_json_blob(getattr(output, "raw", str(output)))
        event_name = TASK_EVENTS.get(name)
        if event_name == "plan":
            plan = parsed
        elif event_name == "specialist_result":
            specialist_results.append(parsed)
        elif event_name == "report":
            report = parsed
    return {
        "plan": plan,
        "specialist_results": specialist_results,
        "report": report,
        "diagnostic": None,
        "stub_data": True,
    }


def run_kickoff(
    symptom: str,
    event_q: queue.Queue[Any] | None = None,
    on_thread_done: Callable[[], None] | None = None,
) -> dict[str, Any]:
    finished = False

    def _finish() -> None:
        nonlocal finished
        if finished:
            return
        finished = True
        if on_thread_done is not None:
            on_thread_done()

    def _do() -> Any:
        try:
            crew = Custsuppcrew().crew()
            if event_q is not None:
                _attach_callbacks(crew, event_q)
            write_trace("kickoff_start", {"symptom_len": len(symptom)})
            return crew.kickoff(inputs={"symptom": symptom})
        finally:
            _finish()

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_do)
    except Exception:
        _finish()
        raise
    try:
        result = future.result(timeout=MAX_EXECUTION_SECONDS)
        snapshot = snapshot_from_result(result)
        write_trace("kickoff_complete", {"ok": True, "usage": _usage_fields(result)})
        return snapshot
    except FuturesTimeout as exc:
        code, message = "CREW_TIMEOUT", "investigation exceeded 600 second cap"
        write_trace("kickoff_error", {"code": code})
        raise CrewRunError(code, message) from exc
    except CrewRunError:
        raise
    except Exception as exc:  # noqa: BLE001 — map to SAD error envelope
        code, message = classify_error(exc)
        write_trace("kickoff_error", {"code": code})
        raise CrewRunError(code, message) from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=False)


class CrewRunError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def start_background(
    symptom: str,
    event_q: queue.Queue[Any],
    on_done: Callable[[dict[str, Any] | None, CrewRunError | None], None],
    on_thread_done: Callable[[], None] | None = None,
) -> None:
    def _worker() -> None:
        try:
            snapshot = run_kickoff(symptom, event_q, on_thread_done=on_thread_done)
            on_done(snapshot, None)
        except CrewRunError as exc:
            event_q.put(
                {
                    "event": "error",
                    "data": {
                        "error": {
                            "code": exc.code,
                            "message": exc.message,
                            "diagnostic": exc.message,
                        }
                    },
                }
            )
            on_done(None, exc)
        finally:
            event_q.put(SENTINEL)

    threading.Thread(target=_worker, daemon=True).start()
