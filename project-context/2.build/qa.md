# QA Log — Unit + Integration

## Summary

- `*test-unit` (2026-08-30): Python unit **22 passed**; FSM **5 passed**.
- `*test-integration` (2026-08-30): investigation API **15 passed**; FE mapper **4 passed**.
- `*verify-flow` (this increment): live stub `:8081` + API `:8000` + Vite `:3000`. SPA-equivalent `POST ?wait=false` + 1500 ms GET poll. Investigation `779496c4-62a1-45b3-bf3b-e504d524688d` **complete** in **287.8s** (192 polls). Plan at **13.6s**. LLM connected. **AC-006 parsed report FAIL** (`report.parse_error`); four heading keys exist only in unparsed `raw`.

No browser click-through (Cursor in-editor browser cannot reach host `:3000`). Open `http://localhost:3000/` in a system browser against this running stack.

## Resolved runtime

`crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`). Adapter: `.cursor/rules/adapter-crewai.mdc`.

## Unit

Command:

```bash
cd custsuppcrew && .venv/bin/pytest -q \
  tests/test_unit_logic.py \
  tests/test_stubs_and_tools.py \
  tests/test_api.py::test_temperature_policy \
  tests/test_api.py::test_kickoff_cap_returns_crew_timeout

cd frontend && npm run test:unit && npm run typecheck
```

| Suite | Tests | Result |
| --- | --- | --- |
| `tests/test_unit_logic.py` | parse/classify/snapshot/flight/fixture/tools/redact/temperature | PASS |
| `tests/test_stubs_and_tools.py` | stub health, fixture source ids, empty tool, 405 mutating POST, bind allowlist | PASS |
| `test_api.py::test_temperature_policy` | Claude allows temperature; gpt-5 does not | PASS |
| `test_api.py::test_kickoff_cap_returns_crew_timeout` | Fake crew + 0.05s cap → `CREW_TIMEOUT` (no LLM) | PASS |
| `frontend` `npm run test:unit` | `runFsm.ts` transitions | PASS (5) |
| `frontend` `npm run typecheck` | — | PASS |

### AC-* mapping (unit)

| AC | Check | Result |
| --- | --- | --- |
| AC-001 | FSM `idle` + `SUBMIT_VALID` → `running` | PASS |
| AC-002 | FSM error/reset returns `idle`; illegal events are no-ops | PASS (FSM only) |
| AC-003 | `TASK_EVENTS["task_plan"] == "plan"` | PASS (mapping only) |
| AC-004 | Snapshot mapper keeps four specialist keys | PASS (mapper only) |
| AC-005 | Stub fixture records expose `id` | PASS (fixture ids) |
| AC-006 | Snapshot report includes four heading keys | PASS (schema keys) |
| AC-007 | Tools bind to stubs; mutating names rejected; stub POST 405 | PASS |
| AC-008 | Fixture CrashLoopBackOff + 3.0× + `stub_data` | PASS |
| AC-009 | No mutating tool names; mutating HTTP rejected | PASS |
| AC-010 | Playbook fixture `executed: false` | PASS (fixture) |
| AC-011 | `__none__` → empty records | PASS |
| AC-012 | `redact()` strips keys / `sk-ant-` / standalone Bearer. Overlap gap remains. | PARTIAL |

### Runtime adapter (crewai) unit checks

| Contract | Result |
| --- | --- |
| YAML task names ↔ `TASK_EVENTS` | PASS |
| `classify_error` codes | PASS |
| Kickoff cap → `CREW_TIMEOUT` | PASS |
| Least-privilege tool bind | PASS |

## Integration

Command:

```bash
cd custsuppcrew && .venv/bin/pytest -q tests/test_api.py
cd frontend && npm run test:integration && npm run typecheck
```

| Suite | Tests | Result |
| --- | --- | --- |
| `tests/test_api.py` | health, validation, CORS, 429, 202 poll, plan-before-complete, LLM failure envelope, oversize/invalid JSON | PASS (15) |
| `frontend` `npm run test:integration` | `mapSnapshot` API JSON → Results fields | PASS (4) |
| Live `GET :8000/health` | process up | **DOWN** (000) — not a TestClient failure |
| Live stub `:8081` / Vite `:3000` | — | **DOWN** |

### FE ↔ API ↔ runtime contract

| Boundary | Check | Result |
| --- | --- | --- |
| API `GET /health` | 200 `{status: ok}` no LLM | PASS |
| API validation | empty / missing / whitespace / 8193 chars / invalid JSON → 400 `VALIDATION_ERROR`; flight not taken | PASS |
| API CORS | OPTIONS from `localhost:3000` and `127.0.0.1:3000` | PASS |
| API concurrency | second POST while busy → 429 `BUSY` | PASS |
| API poll start | `POST ?wait=false` + `Accept: application/json` → **202** `investigation_id` + `stub_data` (does not block like SSE-off JSON) | PASS |
| API AC-003 | GET snapshot shows `plan.steps[].agent` while `status=running` and `report` is null | PASS |
| API failure path | error event → GET `status=failed` + `diagnostic.error.code=LLM_UNAVAILABLE` | PASS |
| API 404 | envelope `{error: {code, message, diagnostic}}`; code is `INTERNAL` (SAD has no `NOT_FOUND`) | PASS (shape) / known code mismatch |
| FE mapper AC-003 | running + plan → `planPreview`, no report sections | PASS |
| FE mapper AC-005/006/010 | complete report → Key Insights / Next Steps (`executed: false`) / empty Critical Alerts / Troubleshooting; source ids | PASS |
| FE mapper AC-011 | `empty_tools` → `no data from {tool}` | PASS |
| FE mapper failure | nested `LLM_UNAVAILABLE` → `error` status + `{code}: {message}` | PASS |

### AC-* mapping (integration)

| AC | Check | Result |
| --- | --- | --- |
| AC-001 | 202 `running` + `investigation_id` on non-empty `wait=false` POST | PASS (API). Live UI still smoke. |
| AC-002 | Empty/whitespace POST 400; client trim is code-level (App.tsx) not re-executed here | PASS (API) |
| AC-003 | Plan on GET while still `running` | PASS |
| AC-004 | Four specialists in mapper fixture; live four-agent kickoff is smoke | PASS (mapper fixture) |
| AC-005 | Source `record_id` in mapped `sources` | PASS (mapper) |
| AC-006 | Four report arrays mapped; empty critical alerts length 0 (UI labels “No findings.” in ResultsView — smoke) | PASS (mapper keys) |
| AC-007–009 | Covered in unit/stub bind; not re-hit via investigation API in this stage | See Unit |
| AC-010 | `next_steps[].executed === false` in mapper | PASS |
| AC-011 | `empty_tools` honest empty | PASS |
| AC-012 | Not re-tested at HTTP layer (no secret in TestClient bodies) | See Unit PARTIAL |

## Smoke / `*verify-flow`

Live stack started for this command (dotenv-loaded; `ANTHROPIC_API_KEY` **set, not logged**; `MODEL=anthropic/claude-sonnet-4-6`). Client matched the SPA: `Origin: http://localhost:3000`, `POST /v1/investigations?wait=false`, 1500 ms `GET` poll, 610s cap.

Symptom (AC-008 fixture): `API response times have degraded 3x in the last hour; payments-api pods in CrashLoopBackOff`.

| Check | Result |
| --- | --- |
| Stub `:8081` health | PASS |
| API `:8000` health | PASS |
| Vite `:3000/` 200 + `#root` | PASS (first script only sampled 200 chars; full HTML confirmed) |
| CORS preflight Vite origin | PASS |
| AC-002 empty POST | PASS 400 `VALIDATION_ERROR` |
| AC-001 start | PASS **202** `779496c4-62a1-45b3-bf3b-e504d524688d` `running` `stub_data=true` |
| Concurrent POST | PASS **429** `BUSY` |
| AC-003 plan while running | PASS **13.6s**, 8 steps, `report` still null |
| Poll terminal | PASS `complete` **287.8s** (192 polls) |
| AC-004 four specialists | PASS kubernetes, logs, metrics, runbooks |
| AC-005 cited insights | PASS 18/18 have tool and/or record_id; 25 `empty_tools` |
| AC-006 parsed report keys | **FAIL** snapshot `report` is `{raw, parse_error: true}` (JSON truncated/unparseable). Raw **text** still contains `key_insights`, `next_steps`, `critical_alerts`, `troubleshooting_steps`. FE mapper will fall back to specialist Key Insights and show **No findings.** for the other three headings. |
| AC-007/009 stub traffic | PASS access log is **GET only** (`/k8s`, `/logs`, `/metrics`, `/runbooks`); no POST/PUT/PATCH/DELETE |
| AC-008 `stub_data` | PASS `true`; fixture CrashLoopBackOff on `/k8s/pods` |
| AC-010 next_steps executed | **N/A / weak** — parsed `next_steps` missing due to AC-006 parse failure (0 structured items) |
| AC-011 empty tools | PASS 25 honest empty_tools on specialists |
| AC-012 traces | PASS new `task_complete` / `kickoff_*` lines; no `sk-ant-` or `ANTHROPIC_API_KEY=` in `backend-trace.jsonl` |
| Browser Inputs → Run → Results | **Not automated** |

**Grounded hits (specialists, not the broken report object):** CrashLoopBackOff / missing ConfigMap narrative present in cited insights. Stub GETs included `get_pod_status`, log search, metrics, `runbook/rb-crashloop-configmap`.

## Defects / coverage gaps

1. **AC-012 redact overlap:** `Authorization: Bearer …` can leave the token (`test_trace_redact_authorization_bearer_overlap`).
2. **404 code `INTERNAL`** not `NOT_FOUND`.
3. **No automated browser driver** for Inputs → Run → Results.
4. **AC-006 live report parse failure** on investigation `779496c4-62a1-45b3-bf3b-e504d524688d`: aggregate output stored as `parse_error` / truncated `raw` (~15k chars, ends mid-string). UI will not get structured Next Steps / Critical Alerts / Troubleshooting from this snapshot.
5. **`system-description.md` and `user-stories` absent.**

## Future work (testing)

Browser E2E, SSE EventSource client, live Kubernetes, Slack/PagerDuty, performance/NFR, durable history (FR-105/FR-106). Harden aggregate JSON parse or max output so AC-006 keys survive into the snapshot.

## Next

- Fix aggregate `parse_json_blob` / task output completeness (AC-006), then re-run `*verify-flow` or `*qa`.
- After QA is accepted, `@security.eng *assess-security` before Deliver (`security.require_security_assessment: true`).

## Sources

1. `project-context/1.define/prd.md` AC-001–AC-012
2. `project-context/2.build/backend.md`
3. `project-context/2.build/frontend.md` / `frontend-functional-spec.md`
4. `project-context/2.build/integration.md`
5. `aamad.config.yml` (`testing.require_integration_tests`, `map_to_acceptance_criteria`)
6. `.cursor/agents/qa-eng.md` (`*test-unit`, `*test-integration`)
7. `.cursor/rules/adapter-crewai.mdc`

## Assumptions

1. `system-description.md` and `user-stories` missing; PRD AC-* are authoritative.
2. FastAPI `TestClient` is the integration harness for the investigation API (no LLM).
3. FE `mapSnapshot` tests are the UI side of the snapshot contract; they do not call `fetch`.
4. In-process stub `TestClient` stays in the Unit section.
5. `AAMAD_TARGET_RUNTIME` unset → `crewai`.

## Open Questions

1. Should `redact()` apply Bearer redaction before the generic `authorization` substitution?
2. ~~Export `mapSnapshot` from `runService.ts`?~~ **Closed:** exported; covered by `npm run test:integration`.
3. Add Vitest later, or keep Node `node:test`?
4. Should 404 use `NOT_FOUND` despite SAD’s listed codes?

## Halt and Report

Live flow ran to `complete`. Blocker for full AC-006 UI report: unparseable aggregate JSON (`parse_error`). Remaining gaps: no browser driver; 404 `INTERNAL`; redact Bearer overlap. Safe retry: keep stack up, fix parser/output, `POST ?wait=false` again.

## Audit

- **Timestamp:** 2026-08-30T10:50:00-04:00
- **Persona id:** `qa-eng`
- **Action:** `test-unit`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Authored `custsuppcrew/tests/test_unit_logic.py` and `frontend/src/fsm/runFsm.test.ts`; pytest 22 passed; Node 24 `test:unit` 5 passed; `tsc -b --noEmit` passed.
- **Prohibited actions:** Did not run live LLM, browser E2E, or performance tests.

- **Timestamp:** 2026-08-30T10:55:00-04:00
- **Persona id:** `qa-eng`
- **Action:** `test-integration`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Extended `tests/test_api.py` (plan-on-poll, LLM failure snapshot, validation/CORS/202); exported `mapSnapshot`; `runService.map.test.ts`; pytest `tests/test_api.py` 15 passed; `npm run test:integration` 4 passed; typecheck passed. Live `:8000/:8081/:3000` down.
- **Prohibited actions:** Did not call Anthropic, Slack, PagerDuty, or a live kube-apiserver. Did not run browser E2E or performance tests.

- **Timestamp:** 2026-08-30T10:57:00-04:00
- **Persona id:** `qa-eng`
- **Action:** `verify-flow`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`). Model env name `anthropic/claude-sonnet-4-6` (value not a secret).
- **Prompt Trace:** Omitted from this artifact. Crew stdout stayed in the local API process; no API keys copied here. Investigation id `779496c4-62a1-45b3-bf3b-e504d524688d`.
- **Tooling:** Started stub-telemetry `:8081`, investigate-api `:8000` (dotenv), Vite `:3000`; SPA-equivalent poll client; live kickoff 287.8s → `complete`; stub GET-only; traces redacted; AC-006 parse_error on report object.
- **Prohibited actions:** Did not call Slack/PagerDuty or live kube-apiserver. Did not log secret values.

- **Timestamp:** 2026-09-05T13:54:24-04:00
- **Persona id:** `qa-eng`
- **Action:** `run-evals`
- **Resolved runtime:** `crewai`
- **Notes:** Eval contract and results live in `project-context/2.build/evals.md`. Offline suite exit 1: EC-003/004/009 (aggregate parse_error), EC-011 (Bearer redact overlap), EC-013 (no historical token fields). Next: `@security.eng *assess-security` before Deliver.
