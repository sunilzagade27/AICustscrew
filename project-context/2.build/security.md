# Security Assessment — MVP SRE Investigation Chat

## Summary

Assessed the CrewAI local MVP (Vite UI + FastAPI investigation API + stub telemetry) after QA `qa.md`. Scope is **localhost demo**, not production pen-test (SAD §8; PRD FR-207 deferred).

**Verdict:** No **Critical** findings in the current bind configuration (API and stubs listen on `127.0.0.1` only). One **High** process risk: an untracked nested CrewAI scaffold that contains a local `.env` must never be committed. Remaining items are Medium/Low/Info and either match SAD AD-09 (unauthenticated local chat) or should be fixed by owning personas before a non-localhost deploy.

Handoff to `@devops.eng` is allowed for **local Deliver packaging** if the operator **accepts** AD-09 and the Vite LAN bind (S-03). Do **not** expose `:8000` / `:8081` beyond loopback until auth exists.

## Resolved runtime

`crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`).

## Config honored

| Key | Value | How applied |
| --- | --- | --- |
| `security.require_security_assessment` | true | This artifact |
| `security.forbid_committed_secrets` | true | Secret scan; `.env.example` names only |
| `security.dependency_audit` | true | `npm audit` (0 vulns); `pip-audit` not installed in `.venv` |

## Findings

Severity: Critical / High / Medium / Low / Info.

### Critical

None.

### High

| ID | Finding | Evidence | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| S-01 | Nested untracked CrewAI scaffold includes a local `.env`. Committing it would violate `forbid_committed_secrets`. | `custsuppcrew/src/custsuppcrew/guide_creator_flow/` (untracked; nested `.git` and `.env`). Not in `git ls-files`. | Do not `git add` that tree. Add a root or `custsuppcrew` gitignore entry. Delete or relocate the scaffold outside the app package. **No secret values recorded here.** | Operator / `@project.mgr` |

### Medium

| ID | Finding | Evidence | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| S-02 | Trace redaction can leave a Bearer token after `Authorization: Bearer …` (AC-012 partial). | `custsuppcrew/src/custsuppcrew/trace_log.py` `redact()`; QA `test_trace_redact_authorization_bearer_overlap`. | Apply Bearer redaction **before** the generic `authorization` substitution, or redact remaining tokens after. | `@backend.eng` |
| S-03 | Vite `server.host: true` binds all interfaces (LAN URL was advertised in dev). UI is reachable off-loopback while the API stays on `127.0.0.1`. If `VITE_API_BASE_URL` is set empty, the Vite proxy would forward `/v1` and `/health` from any client that can reach `:3000`. | `frontend/vite.config.ts`; default `frontend/.env.example` uses `http://127.0.0.1:8000` (direct, not proxy). | For local-only demo: `host: "127.0.0.1"`. Keep a non-empty API base URL or bind Vite to loopback. Do not combine `host: true` + empty `VITE_API_BASE_URL` + public network. | `@frontend.eng` / `@integration.eng` |
| S-04 | Unauthenticated `POST /v1/investigations` spends LLM budget. SAD AD-09 allows this **on localhost**. Binding `investigate-api` to `0.0.0.0` later would make this High/Critical. | `custsuppcrew/src/custsuppcrew/api.py` `run_api()` `host="127.0.0.1"`; CORS localhost origins; no `DEMO_API_TOKEN`. | Keep loopback bind. Before any LAN/cloud expose: shared secret or bind firewall. Optional `DEMO_API_TOKEN` remains SAD Open Question. | `@backend.eng` (code) / `@devops.eng` (deploy bind) |
| S-05 | Crew `verbose=True` writes investigation content (symptoms, tool JSON) to process stdout. Not the API-key path, but incident text is not treated as sensitive in the TTY. | `custsuppcrew/src/custsuppcrew/crew.py` and `config/agents.yaml` `verbose: true`. | Set verbose false for shared machines; keep traces in redacted `backend-trace.jsonl` only. | `@backend.eng` |

### Low

| ID | Finding | Evidence | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| S-06 | `frontend/.gitignore` does not ignore `.env`; repo has **no root `.gitignore`**. A Vite `.env` could be added accidentally. | `frontend/.gitignore` (`node_modules`, `dist`, `*.local` only). `custsuppcrew/.gitignore` does ignore `.env`. | Ignore `.env` in `frontend/` and add a root gitignore. | `@project.mgr` / `@frontend.eng` |
| S-07 | CORS `allow_headers=["*"]` with a tight origin list. Fine for local MVP; overly open if origins expand. | `custsuppcrew/src/custsuppcrew/api.py` | Restrict to `Content-Type`, `Accept`. | `@backend.eng` |
| S-08 | Stub client embeds `httpx` error strings in tool JSON returned to the LLM (`STUB_UNAVAILABLE` + exception text). | `custsuppcrew/src/custsuppcrew/tools/stub_client.py` | Return a generic unavailable message; omit raw exception. | `@backend.eng` |
| S-09 | User symptom (max 8192) is LLM prompt input (prompt-injection surface). Mutating HTTP is not bound; residual risk is **misleading report text**, not cluster writes. | `api.py` `SYMPTOM_MAX`; `read_only_tools.py`; QA AC-007/009 GET-only stub log. | Keep tool allowlist; do not add mutating tools. Guardrails already on aggregate `expected_output`. | `@backend.eng` (no product change required for MVP) |
| S-10 | Live aggregate report stored as `parse_error` (QA AC-006). Integrity of the cited report object, not an auth bypass. | `qa.md` `*verify-flow`; investigation `779496c4-62a1-45b3-bf3b-e504d524688d`. | Harden JSON parse / output size (`parse_json_blob`). | `@backend.eng` |

### Info (accepted / in-policy)

| ID | Note |
| --- | --- |
| I-01 | SAD AD-09: unauthenticated local chat; no SSO. Matches PRD. |
| I-02 | TLS not required for localhost (SAD §8). |
| I-03 | Investigation API and stubs bind `127.0.0.1` (`api.py` `:8000`, `stubs/app.py` `:8081`). |
| I-04 | Tools are GET-only; stub app has no POST/PUT/PATCH/DELETE telemetry routes; `allow_delegation: false`; `memory=False`; `max_iter: 12`; `max_rpm=10`; process single-flight (`FLIGHT`). |
| I-05 | `.env.example` files list **names** only (`custsuppcrew/.env.example`, `frontend/.env.example`). No `*.env` in `git ls-files`. |
| I-06 | `npm audit` (prod + dev): **0 vulnerabilities**. Python `pip-audit` **not installed**; `uv.lock` is committed. |
| I-07 | Traces under `project-context/2.build/logs/backend-trace.jsonl` are event metadata (task/agent/error code); QA found no `sk-ant-` or `ANTHROPIC_API_KEY=` substrings. |
| I-08 | Optional `DEMO_API_TOKEN` / `GATEWAY_ACCESS_TOKEN` commented in `.env.example` and unused in code. |
| I-09 | No CSP / security headers on the Vite SPA — acceptable for local static demo. |

## Secret scan

| Check | Result |
| --- | --- |
| Tracked `*.env` | None |
| Tracked PEMs / credential files | None |
| `.env.example` values | Empty key placeholders; model **name** only |
| Code literals | Test fixtures use fake `sk-ant-examplevalue123` in `tests/test_unit_logic.py` (not a live key) |
| `custsuppcrew/AGENTS.md` | Documents `OPENAI_API_KEY=sk-...` as a **pattern**, not a credential |
| Nested `guide_creator_flow/.env` | Present on disk, **untracked** — S-01 |

## Dependency notes

| Stack | Pin / lock | Audit |
| --- | --- | --- |
| Frontend | `frontend/package-lock.json`; React 19, Vite 6 | `npm audit` → 0 |
| Backend | `custsuppcrew/uv.lock`; CrewAI `>=1.15.17,<2`, FastAPI, uvicorn, httpx | `pip-audit` missing in `.venv` — **gap vs `dependency_audit: true` for Python** |

Recommend `@devops.eng` run `pip-audit` or `uv pip audit` in CI (Deliver), without changing crew logic.

## Positive controls (MVP)

- Least-privilege YAML tool catalog; mutating name fragments rejected at bind.
- Symptom validation (empty / 8192 cap) before single-flight acquire.
- CORS allowlist limited to local Vite/Next ports.
- Kickoff cap 600s in `investigation.py` independent of hung executor.
- Stub data labeled `stub_data`; UI stub banner (integrity vs mistaking demo for prod).

## Sources

1. `project-context/2.build/qa.md`
2. `project-context/2.build/backend.md`
3. `project-context/2.build/frontend.md`
4. `project-context/2.build/integration.md`
5. `project-context/1.define/prd.md` (auth deferred; `forbid_committed_secrets`)
6. `project-context/1.define/sad.md` §4–§8, AD-09–AD-11
7. `aamad.config.yml` security keys
8. `.cursor/agents/security-eng.md` (`*assess-security`)
9. Code: `api.py`, `trace_log.py`, `stub_client.py`, `read_only_tools.py`, `crew.py`, `vite.config.ts`, gitignores

## Assumptions

1. Target is **local MVP** (SAD AD-09). Unauthenticated loopback API (S-04) is an **accepted risk** with owner = operator, rationale = PRD/SAD no SSO for demo.
2. Vite LAN bind (S-03) is accepted for this branch unless the operator wants loopback-only UI.
3. S-01 is closed for git as long as `guide_creator_flow/` stays untracked; it becomes Critical if committed with a real `.env`.
4. `system-description.md` absent; no extra auth requirement invented.
5. No production pen-test, no live cluster credentials in scope.

## Open Questions

1. Should Deliver bind Vite to `127.0.0.1` only (close S-03)?
2. Enable optional `DEMO_API_TOKEN` before any non-loopback API bind?
3. Add `pip-audit` / `npm audit` to the CI scaffold in `deploy.md`?
4. Should `@backend.eng` fix S-02 and S-10 before Deliver, or accept for local demo?

## Halt and Report

None for local Deliver **if** S-01 remains untracked and S-03/S-04 are accepted. **Halt cloud/LAN API expose** until S-04 has a token or equivalent.

## Audit

- **Timestamp:** 2026-08-30T11:50:00-04:00
- **Persona id:** `security-eng`
- **Action:** `assess-security` (includes `scan-secrets` and `review-deps` checks)
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution in this increment; no secret values copied into this artifact.
- **Tooling:** Read PRD/SAD/qa/backend/frontend/integration; inspected API/CORS/bind, tools, redact, gitignores, lockfiles; `git ls-files` for `*.env`; `npm audit` (0); `pip-audit` unavailable.
- **Prohibited actions:** Did not modify application or agent business logic. Did not commit or paste secret values. Did not expand to production pen-test.
