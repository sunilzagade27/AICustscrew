# Integration Log — MVP Investigation Chat Flow

## Summary

Wired the Vite Critical Research Workflow UI to the CrewAI investigation API. The frontend FSM is unchanged (`idle` → `running` → `done`). `frontend/src/services/runService.ts` calls:

- `POST /v1/investigations?wait=false` → 202 `{ investigation_id, status: running }` (mapped to FE `runId`)
- `GET /v1/investigations/{id}` until `status` is `complete` or `failed`

This increment (`*integrate-api`, 2026-08-28) maps the snapshot `report` into the Results panel using PRD AC-006 headings, drives the stub banner from `stub_data`, binds Vite so both `localhost` and `127.0.0.1` serve `:3000`, and labels Slack/PagerDuty/auto-remediation as Future Work.

No Slack, PagerDuty, live Kubernetes, or other third-party APIs. Default streaming (SSE) is not consumed by the UI; polling matches the existing Run panel.

## Resolved runtime

`crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`). Adapter: `.cursor/rules/adapter-crewai.mdc`.

## Contract mapping

| FE service | HTTP | Backend | Notes |
| --- | --- | --- | --- |
| Client trim / empty check | none | — | AC-002: empty submit never calls `startRun` |
| `startRun({ symptom })` | `POST /v1/investigations?wait=false` body `{ symptom }` | 202 snapshot | `investigation_id` → `runId` |
| `getRunStatus(runId)` | `GET /v1/investigations/{id}` | in-memory snapshot | poll 1500 ms; client abort 610 s |
| Results headings | snapshot `report` | `key_insights`, `next_steps`, `critical_alerts`, `troubleshooting_steps` | empty → “No findings.” |
| — | default POST SSE | not used by UI | available for later chat composer |
| — | `Accept: application/json` blocking POST | not used by UI | would freeze the SPA |

### Payload schema

**Start request:** `{ "symptom": string }` (trimmed, 1–8192 chars).

**Start 202:** `{ investigation_id, status: "running", plan, specialist_results, report, diagnostic, stub_data }`.

**Poll snapshot `status`:**

| Backend | FE `GetRunStatusResponse.status` |
| --- | --- |
| `running` | `running` (optional `planPreview` from `plan.steps`) |
| `complete` | `done` — AC-006 sections from `report`; Key Insights fallback is `specialist_results[].insights` |
| `failed` | `error` — message from `diagnostic.error.message` or string diagnostic |

**Error envelope (400/429/404/502):** `{ error: { code, message, diagnostic } }` shown as `{code}: {message}` (e.g. `BUSY: another investigation is already running`, `VALIDATION_ERROR: …`).

### CORS / origin

Backend CORS allows `http://localhost:3000`, `http://127.0.0.1:3000`, and the same hosts on `:5173`. Vite `server.port` is **3000**, `host: true`, `strictPort: true` so both loopback names serve the SPA. Default `VITE_API_BASE_URL=http://127.0.0.1:8000`. Vite also proxies `/v1` and `/health` to `:8000` if `VITE_API_BASE_URL` is set to empty (same-origin).

## Code changes

| Path | Change |
| --- | --- |
| `frontend/src/services/runService.ts` | Live fetch client + snapshot mapper (findings, AC-006 report sections, nested diagnostic) |
| `frontend/src/App.tsx` | 1500 ms poll, immediate first poll, 610 s timeout, plan preview, Future Work label |
| `frontend/src/components/RunStatus.tsx` | Supervisor plan while running (FR-002); stub banner |
| `frontend/src/components/ResultsView.tsx` | AC-006 headings; empty sections labeled No findings; stub banner from `stubData` |
| `frontend/src/components/InputsForm.tsx` | Neutral symptom placeholder (AC-008: do not hard-code AWS demo story) |
| `frontend/vite.config.ts` | Dev proxy `/v1`, `/health` → `:8000`; `host: true`; `strictPort: true` |
| `frontend/.env.example` | `VITE_API_BASE_URL` name only |
| `custsuppcrew/tests/test_api.py` | CORS preflight for Vite origins |
| `project-context/2.build/frontend-functional-spec.md` | Results §3 + poll/dev-server contract |

## How to run locally

```bash
# terminal 1
cd custsuppcrew && source .venv/bin/activate && stub-telemetry

# terminal 2
cd custsuppcrew && source .venv/bin/activate && investigate-api

# terminal 3
cd frontend && npm install && npm run dev
```

Open `http://localhost:3000` or `http://127.0.0.1:3000`. Submit a non-empty symptom. Expect Run panel (`runId` = investigation UUID), plan text when the supervisor task completes, stub banner, then Results with Key Insights / Next Steps / Critical Alerts / Troubleshooting Steps. Telemetry is fixture data (`stub_data: true`).

## Verification (`*verify-messageflow`, 2026-08-26)

Live stack: stub-telemetry `:8081`, investigate-api `:8000` (dotenv-loaded `MODEL=anthropic/claude-sonnet-4-6`; provider key **present, not logged**), Vite `http://localhost:3000/`. No browser driver in this session; the client used the **same contract as the SPA** (`Origin: http://localhost:3000`, `POST ?wait=false`, 1500 ms `GET` poll, FE findings mapper).

Symptom (stub fixture, AC-008): `API response times have degraded 3x in the last hour; payments-api pods in CrashLoopBackOff`.

| Check | Result |
| --- | --- |
| Stub + API health | PASS |
| Stub fixture includes CrashLoopBackOff + `stub_data` | PASS |
| Vite index `GET http://localhost:3000/` | PASS (200) |
| CORS preflight OPTIONS from Vite origin | PASS (`access-control-allow-origin: http://localhost:3000`) |
| AC-002 server: empty/whitespace POST | PASS 400 `VALIDATION_ERROR` |
| AC-002 client: empty submit | PASS by code inspection — `App.tsx` returns before `startRun` |
| AC-001 start | PASS **202** `investigation_id=bffae565-f10c-423f-8a72-f9effd71daee` `status=running` `stub_data=true` |
| Concurrent second POST | PASS **429** `BUSY` |
| AC-003 plan on poll before complete | PASS plan at **13.6s** (still `running`, 0 specialists yet) |
| Poll terminal | PASS `complete` in **266.6s** (178 polls) |
| AC-004 four specialists | PASS kubernetes, logs, metrics, runbooks |
| AC-005 cited findings (mapper) | PASS 28/28 findings have tool and/or record_id (or explicit `empty_tools`) |
| AC-006 report keys on snapshot | PASS `key_insights`, `next_steps`, `critical_alerts`, `troubleshooting_steps` |
| AC-007/009 this run | PASS stub access log shows **GET only** (`/k8s`, `/logs`, `/metrics`, `/runbooks`); no POST/PUT/PATCH/DELETE |
| AC-008 `stub_data` | PASS `true` on snapshot |
| FE mapper → Results | PASS summary grounded in pod CrashLoopBackOff / missing ConfigMap |
| `npm run typecheck` | PASS |
| Browser click Inputs → Run → Results | **Not automated** (no browser tool). Open `http://localhost:3000/` against the running stack to confirm visually. |

**Observed tool traffic (stubs):** `get_pod_status`, `get_node_status`, `get_deployment_status`, `get_cluster_events`, `search_logs`, `count_log_patterns`, `get_performance_metrics`, `get_error_metrics`, `get_availability_metrics`, `search_runbooks`, `get_playbook`, `get_escalation_procedure`. Grounded hits include `pod/payments-api-7f9c-abc` CrashLoopBackOff, `metric/p99-latency-1h` 3.0×, `runbook/rb-crashloop-configmap`. Extra searches that miss the fixture are listed under `empty_tools` (honest empty, not invented rows).

**UI vs PRD AC-006 (closed 2026-08-28):** Results now renders the four AWS-style section headings. Session History is still in-memory only.

## Not integrated (out of MVP)

Slack, PagerDuty, live cluster credentials, SSE EventSource client, Next.js App Router migration, durable history (FR-105/FR-106).

## Sources

1. `project-context/1.define/prd.md` FR-001–FR-008, AC-001–AC-002, AC-006, AC-008
2. `project-context/1.define/sad.md` §3–§4 (investigation API, CORS, poll vs SSE, CitedReport)
3. `project-context/2.build/backend.md` API contract
4. `project-context/2.build/frontend.md` / `frontend-functional-spec.md` FSM + `startRun`/`getRunStatus`
5. `.cursor/rules/adapter-crewai.mdc`
6. `.cursor/agents/integration-eng.md` (`*integrate-api`)
7. `aamad.config.yml` `runtime.target: crewai`

## Assumptions

1. `setup.md` absent; proceeded from PRD/SAD/backend.md/frontend.md.
2. Polling (`wait=false` + GET) is the MVP UI mode; SSE remains backend-default for other clients.
3. Vite SPA on `:3000` is acceptable vs SAD Next.js `:3000` for this wiring (same origin slot).
4. Plan preview is best-effort from `plan.steps`; malformed crew JSON yields empty preview until report.
5. History stays session-local; selecting a history row does not re-kick the crew.
6. Investigation API + stub-telemetry + Vite were running during `*verify-messageflow` (2026-08-26). This increment did not re-run a live crew kickoff.
7. If snapshot `report.key_insights` is empty, Key Insights falls back to specialist findings so the Results panel is not blank after a complete run.

## Open Questions

1. Produce `setup.md` before Deliver?
2. Consume SSE in the UI later (token-ish specialist updates) vs keep polling?
3. Should 404 use `NOT_FOUND` instead of `INTERNAL`? (backend as-is; SAD error-code list does not include `NOT_FOUND`; FE shows the envelope.)
4. Operator confirm Vite vs migrate to Next.js before Deliver?
5. ~~Run `*verify-messageflow` with stub-telemetry + LLM for a full cited report in the browser.~~ **Closed:** live 202+poll round-trip completed (`complete` in 266.6s). Browser click-through still operator-optional; re-run `*verify-messageflow` after AC-006 Results mapping if visual confirmation is required.
6. ~~Should ResultsView render PRD AC-006 headings (Key Insights / Next Steps / Critical Alerts / Troubleshooting Steps) instead of (or in addition to) Summary / Findings / Sources?~~ **Closed:** Results renders the four headings; Sources remains as a citation index.
7. ~~Bind Vite to `127.0.0.1` as well as localhost so both origins in the CORS list actually serve the SPA?~~ **Closed:** `server.host: true` + `strictPort: true`.

## Halt and Report

None. HTTP wiring and AC-006 Results mapping are in place. Residual gaps: no automated browser driver; `setup.md` still missing (not owned by this persona). Next optional action: `*verify-messageflow`.

## Audit

- **Timestamp:** 2026-08-26T15:55:00-04:00
- **Persona id:** `integration-eng`
- **Action:** `integrate-api`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution in this increment; no secret values copied into artifacts.
- **Tooling:** Replaced FE stub services with fetch to SAD investigation endpoints; Vite proxy + `.env.example`; `npm run typecheck` pass; curl health/400/404 against local `:8000`.
- **Prohibited actions:** Did not integrate Slack/PagerDuty/live cluster. Did not add durable history or change crew/tools.

- **Timestamp:** 2026-08-26T11:52:00-04:00
- **Persona id:** `integration-eng`
- **Action:** `verify-messageflow`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`). Model env name `anthropic/claude-sonnet-4-6` (value not a secret).
- **Prompt Trace:** Omitted from this artifact. Crew stdout remained in the local API process; no API keys copied here. Investigation id `bffae565-f10c-423f-8a72-f9effd71daee`.
- **Tooling:** Started stub-telemetry + investigate-api (dotenv) + Vite; FE-equivalent poll client against `POST /v1/investigations?wait=false` and `GET /v1/investigations/{id}`; CORS from `http://localhost:3000`; live kickoff 266.6s → `complete`, fail_count 0; nested diagnostic mapper fix; `npm run typecheck` pass.
- **Prohibited actions:** Did not call Slack/PagerDuty or live kube-apiserver. Did not log secret values.

- **Timestamp:** 2026-08-28T12:20:00-04:00
- **Persona id:** `integration-eng`
- **Action:** `integrate-api`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution in this increment; no secret values copied into artifacts.
- **Tooling:** Mapped snapshot `report` to AC-006 Results headings; stub banner from `stub_data`; Vite `host: true` / `strictPort: true`; CORS preflight pytest; Future Work labels; `npm run typecheck` and `pytest` on API tests.
- **Prohibited actions:** Did not integrate Slack/PagerDuty/live cluster. Did not add durable history, SSE client, or change crew/tools.
