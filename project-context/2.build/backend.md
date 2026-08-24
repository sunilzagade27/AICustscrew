# Backend Build Log — SRE Investigation Crew

## Summary

MVP CrewAI backend for the investigation-first SRE assistant: five YAML agents, sequential tasks, **read-only stub telemetry tools**, and FastAPI investigation endpoints (SSE + JSON snapshot). No live cluster, no mutating tools, no database.

## Actions

| Action | Status |
| --- | --- |
| `*define-agents` | Done (prior increment) |
| `*develop-be` | Done — stub OpenAPI surfaces + GET-only CrewAI tools bound per specialist |
| `*implement-endpoint` | Done — `GET /health`, `POST /v1/investigations`, `GET /v1/investigations/{id}` |
| `*document-backend` | Done — this file |
| `*stub-nonmvp` | Not run as a command; leftover template YAML files remain unused |

## Resolved runtime

`crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`). CrewAI **1.15.17**. LLM wrapper: `MODEL` env default `anthropic/claude-sonnet-4-20250514`, **temperature 0.1**. AgentCore is not an AAMAD runtime.

## Deliverables

| Path | Role |
| --- | --- |
| `custsuppcrew/src/custsuppcrew/config/agents.yaml` | Five MVP agents |
| `custsuppcrew/src/custsuppcrew/config/tasks.yaml` | Six sequential tasks |
| `custsuppcrew/src/custsuppcrew/crew.py` | YAML crew; tools + LLM bound |
| `custsuppcrew/src/custsuppcrew/stubs/app.py` | Read-only stub OpenAPI on `:8081` |
| `custsuppcrew/src/custsuppcrew/stubs/data.py` | Synthetic fixture (3x latency / CrashLoopBackOff / missing ConfigMap) |
| `custsuppcrew/src/custsuppcrew/tools/read_only_tools.py` | 12 GET-only tools |
| `custsuppcrew/src/custsuppcrew/api.py` | Investigation API on `:8000` |
| `custsuppcrew/src/custsuppcrew/investigation.py` | Kickoff + 600s timeout + event mapping |
| `custsuppcrew/.env.example` | Env **names** only |
| `custsuppcrew/tests/test_stubs_and_tools.py` | AC-007/009/011-oriented stub/tool tests |
| `custsuppcrew/tests/test_api.py` | AC-002 health/validation/429 tests |

## Agent / tool binding

| Agent | Tools |
| --- | --- |
| `supervisor` | none |
| `kubernetes_specialist` | `get_pod_status`, `get_node_status`, `get_deployment_status`, `get_cluster_events` |
| `logs_specialist` | `search_logs`, `count_log_patterns` |
| `metrics_specialist` | `get_performance_metrics`, `get_error_metrics`, `get_availability_metrics` |
| `runbooks_specialist` | `search_runbooks`, `get_playbook`, `get_escalation_procedure` |

Tools issue **HTTP GET only** to `STUB_*_BASE_URL` (default `http://127.0.0.1:8081`). Mutating method names are rejected at bind time. Stub app has no POST/PUT/PATCH/DELETE routes for telemetry.

## API contract (SAD §4)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | Liveness; no LLM |
| POST | `/v1/investigations` | Body `{ "symptom": string }`; empty/whitespace → 400 `VALIDATION_ERROR` (AC-002); max 8192 chars |
| GET | `/v1/investigations/{id}` | In-process snapshot |

POST default: SSE events `started`, `plan`, `specialist_result`, `report`, `error`. JSON snapshot: `Accept: application/json` or `?stream=false`. One investigation per process (429 if busy). Kickoff timeout 600s → `CREW_TIMEOUT`. LLM/auth failures → `LLM_UNAVAILABLE`.

Redacted traces: `project-context/2.build/logs/backend-trace.jsonl`.

## How to run locally

```bash
cd custsuppcrew
source .venv/bin/activate
stub-telemetry          # :8081
investigate-api         # :8000  (separate terminal)
```

JSON example: `curl -H 'accept: application/json' -d '{"symptom":"..."}' http://127.0.0.1:8000/v1/investigations?stream=false`

Tests: `cd custsuppcrew && .venv/bin/pytest -q` (11 passed; no LLM kickoff).

## Frontend gap (for `@integration.eng`)

Vite FE stubs poll `startRun` / `getRunStatus` with `runId`. Backend uses SAD `investigation_id` + SSE/JSON snapshot. Do not wire FE in this epic.

## Not implemented / Future Work

Live k8s/log/metrics/runbook connectors (FR-101); AgentCore (FR-102); plan edit; memory; mutating tools; Slack/PagerDuty; SSO; durable store. Unused `config/agentsSRE.y` / `tasksSRE.y`. `setup.md` still missing.

## Sources

1. `project-context/1.define/prd.md` FR-001–FR-008, AC-001–AC-012
2. `project-context/1.define/sad.md` §2–§4, AD-07, AD-10, AD-11
3. `.cursor/rules/adapter-crewai.mdc`
4. `.cursor/agents/backend-eng.md`
5. `aamad.config.yml`
6. CrewAI 1.15.17 (`BaseTool`, `@CrewBase`, sequential `Crew`)

## Assumptions

1. `setup.md` still absent; proceeded from PRD/SAD.
2. One stub process on `:8081` hosts four OpenAPI prefixes (AD-07).
3. Fixture narrative is synthetic and labeled `stub_data` (AC-008); not customer truth.
4. Exact model id defaults to `anthropic/claude-sonnet-4-20250514` via `MODEL`; override in `.env`.
5. CORS allows local Vite (`5173`) and SAD Next.js (`3000`).
6. 429 busy uses error code `INTERNAL` (SAD enum has no BUSY code).

## Open Questions

1. Produce `setup.md` before Deliver?
2. Delete unused `agentsSRE.y` / `tasksSRE.y`?
3. Should 429 use a dedicated code, or keep `INTERNAL`?
4. Align FE poll contract vs SAD SSE in integration epic?

## Audit

- **Timestamp:** 2026-08-24T19:55:00-04:00
- **Persona id:** `backend-eng`
- **Action:** `develop-be`, `implement-endpoint`, `document-backend`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset). CrewAI 1.15.17. LLM temperature 0.1; default model `anthropic/claude-sonnet-4-20250514`.
- **Prompt Trace:** Omitted from this artifact. Runtime traces (redacted) go to `project-context/2.build/logs/backend-trace.jsonl` on kickoff. No customer systems contacted. Did not read `.env` secret values.
- **Tooling:** Implemented stub FastAPI + GET tools + investigation API; `uv add fastapi uvicorn httpx pytest`; `.venv/bin/pytest -q` → 11 passed; instantiated `Custsuppcrew().crew()` and verified tool names. No live `kickoff()` (would call Anthropic).
- **Determinism:** Fixture JSON is static. Crew outputs remain LLM-dependent.
- **Config honored:** Python/CrewAI, no committed secrets, files under 400 lines, unit tests mapped to AC-002/007/009/011.
- **Prohibited actions:** No database, analytics, live cluster credentials, or mutating tools.
