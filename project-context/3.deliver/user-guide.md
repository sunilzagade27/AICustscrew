# User Guide — SRE Investigation Assistant (`0.1.0`)

Installation guide and end-user manual for the local MVP. Derived from PRD, integration.md, deploy.md, and qa.md. `setup.md` is missing; install steps come from `backend.md` / `integration.md` / the deploy runbook.

## 1. Product Overview

This product is an **investigation-first** multi-agent SRE assistant. You paste an alert or type a symptom. A supervisor writes a plan, then Kubernetes, logs, metrics, and runbooks specialists read **stub** telemetry. The UI shows a plan, then a cited report under Key Insights, Next Steps, Critical Alerts, and Troubleshooting Steps. Agents do **not** restart pods, scale, apply manifests, or otherwise mutate a cluster.

It is for **on-call SREs and platform engineers** who want faster time-to-context during an incident. It does not replace PagerDuty, Slack, Datadog, or `kubectl`. Engineering-manager / executive reporting is deferred.

**MVP limitations (do not treat as production IR):**

- Telemetry is fixture data (`stub_data`). The UI banner says it is not live cluster telemetry.
- Localhost only, unauthenticated (SAD AD-09). Do not expose `:8000` off loopback.
- One investigation at a time. History is session-only (lost on refresh).
- Live aggregate JSON often fails to parse (QA AC-006). Results may show specialist Key Insights and **No findings.** for other headings.
- No Slack, PagerDuty inbound, SSO, live cluster connectors, or auto-remediation.
- UI is a Vite single-route form (Inputs → Run → Results), not the SAD Next.js chat composer.

## 2. Prerequisites

| Need | Detail |
| --- | --- |
| OS | Developer laptop or single small VM (macOS / Linux assumed). |
| Python | 3.10–3.13 with `uv` (Compose image uses 3.12). |
| Node.js | 22 and npm (Vite UI). |
| Optional | Docker Compose, if you use the packaged stack. |
| Account | Anthropic API access. Set env var **name** `ANTHROPIC_API_KEY` locally. Never commit the value. |
| Browser | A current desktop browser that can open `http://127.0.0.1:3000` (Chrome, Safari, or Firefox). No in-app browser requirement. |
| Ports | `127.0.0.1:3000` (UI), `:8000` (API), `:8081` (stubs). |

`aamad.config.yml` selects runtime `crewai`. You do not edit that file to run the demo.

## 3. Installation

`setup.md` does not exist. Use one of the two paths in `project-context/3.deliver/deploy.md`.

### Configuration

1. Copy `custsuppcrew/.env.example` to `custsuppcrew/.env`.
2. Set `ANTHROPIC_API_KEY` on your machine only.
3. Optional: `MODEL` (example name `anthropic/claude-sonnet-4-20250514`), `LLM_TEMPERATURE` (`0.1`).
4. Leave stub URLs at `http://127.0.0.1:8081` for local processes. Compose overrides them to `http://stubs:8081`.
5. Frontend: `VITE_API_BASE_URL=http://127.0.0.1:8000` (`frontend/.env.example`).
6. Do not commit `.env`. Do not add `custsuppcrew/src/custsuppcrew/guide_creator_flow/` to git.

### Local processes (developer path)

```bash
cd custsuppcrew && uv sync --frozen --group dev
source .venv/bin/activate
stub-telemetry          # terminal 1 — :8081
investigate-api         # terminal 2 — :8000 (loads .env)

cd frontend && npm ci && npm run dev   # terminal 3 — :3000
```

### Compose (packaged path)

Only after you intend to start containers:

```bash
docker compose --env-file custsuppcrew/.env up --build
```

### Verify health / smoke check

| Check | Expect |
| --- | --- |
| `curl -sS http://127.0.0.1:8081/health` | HTTP 200 |
| `curl -sS http://127.0.0.1:8000/health` | HTTP 200 |
| Open `http://127.0.0.1:3000/` | HTTP 200, Inputs form |
| Submit empty symptom | Inline validation; no kickoff |
| Empty `POST` to `/v1/investigations` | 400 `VALIDATION_ERROR` |

Health does not need `ANTHROPIC_API_KEY`. A live run does.

## 4. Getting Started

All UI is on one route: `http://127.0.0.1:3000/`.

1. Confirm the stub banner will appear after a run: **Demo / stub data — not live cluster telemetry.**
2. On **Inputs**, enter a non-empty symptom (max 8192 characters). Fixture text used in QA:

   `API response times have degraded 3x in the last hour; payments-api pods in CrashLoopBackOff`

3. Submit. The FSM goes `idle` → `running`. The **Run** panel shows status, an investigation UUID (`runId`), and “Investigation in progress…”.
4. When the supervisor finishes, a plan preview can appear before the run completes (often ~10–15s when the LLM is up).
5. Wait for **Results** (`done`). A full crew run may take several minutes (QA live run ~5 minutes; hard cap 600 seconds).
6. Read the four headings. Citations / source IDs appear when the report parses. If the aggregate JSON fails, Key Insights may fall back to specialist lines; other headings may say **No findings.**
7. Use **New research run** to return to Inputs. Session **History** lists completed runs; selecting a row re-shows that snapshot and does **not** start a new crew.

Do not start a second investigation until the first finishes (`429 BUSY`).

## 5. Everyday Use

| Task | What to expect |
| --- | --- |
| Investigate a pasted alert | Plan, then four specialist passes, then a cited report. Next steps are instructions, not executed actions (`executed: false` on playbook fixtures). |
| Re-read a finished run | History on the same page. Refreshing the browser clears History. |
| Interpret citations | Source IDs such as pod/metric/runbook fixture names. Extra tool searches can be `empty_tools` (honest empty, not invented rows). |
| See Future Work labels | Slack, PagerDuty, durable history, similar-incident lookup — labels only, not features. |

**Errors you may see**

| Code / UI | Meaning | What you do |
| --- | --- | --- |
| Empty submit / `VALIDATION_ERROR` | Symptom missing or over 8192 chars | Fix the text; no LLM call. |
| `BUSY` / 429 | Another investigation is running | Wait or stop the API (see rollback). |
| `LLM_UNAVAILABLE` | Missing/invalid key or provider down | Check `ANTHROPIC_API_KEY` locally; retry later. |
| `CREW_TIMEOUT` | Hit the 600s cap | Retry; shorten the symptom if needed. |
| `BUDGET_EXCEEDED` | Iteration / RPM budget | Retry later; do not raise caps in the UI. |
| `INTERNAL` | Other failure, including unknown investigation id (404 uses this code) | Check API logs; start a new run. |
| **No findings.** on some headings | Often AC-006 parse gap | Use Key Insights / specialist lines; do not invent RCA. |

Treat every finding as a **hypothesis to verify**. You own severity, comms, and any cluster change.

## 6. Troubleshooting

| Symptom | Remediation |
| --- | --- |
| `ERR_CONNECTION_REFUSED` on `:3000` | Start Vite (`npm run dev`) or Compose frontend. Cursor’s in-editor browser may not reach host localhost; use the system browser. |
| API or stubs down | Start `investigate-api` and `stub-telemetry`, or `docker compose up`. Confirm health URLs. |
| UI loads, kickoff fails immediately | Key unset → `LLM_UNAVAILABLE`. Health can still be 200. |
| Compose API cannot reach stubs | Do not point container `STUB_*_BASE_URL` at `127.0.0.1`. Compose must use `http://stubs:8081`. |
| Port already in use | Stop the other stack (Compose vs local processes) on 3000/8000/8081. |
| Vite shows a LAN URL | Prefer `http://127.0.0.1:3000`. Do not combine LAN UI with an exposed API. |
| Results look incomplete | Known AC-006 gap. Check snapshot `report.parse_error` via `GET /v1/investigations/{id}`. |

**Logs (no secret values):**

- API / crew stdout in the `investigate-api` terminal (verbose crew output possible).
- Redacted traces: `project-context/2.build/logs/` (for example `backend-trace.jsonl`).
- Compose: `docker compose logs api stubs frontend`.

## 7. Deployment Notes (operators)

Full runbook: `project-context/3.deliver/deploy.md` (hosting, env matrix, access control, promotion, rollback).

- Host: laptop Compose or three processes. Host publish is `127.0.0.1` only.
- CI (`.github/workflows/ci.yml`) lints, tests, and builds. It does **not** deploy.
- Promotion is manual: CI green, then operator-authorized `docker compose --env-file custsuppcrew/.env up --build`.
- **Rollback:** `docker compose stop api` or stop `investigate-api`. Incident response stays on existing PagerDuty/Slack. There is no agent-applied cluster rollback.
- Do not publish API/stubs off loopback until a shared secret (`DEMO_API_TOKEN` is still an open SAD question) exists.

## Sources

1. `project-context/1.define/prd.md` (personas, investigation-first scope, AC-006 headings)
2. `project-context/1.define/sad.md` §3–§5 (UI, API, AD-09, Compose)
3. `project-context/2.build/integration.md` (local run, fixture symptom, verify flow)
4. `project-context/2.build/backend.md` (API codes, 600s cap)
5. `project-context/2.build/frontend.md` / `frontend-functional-spec.md` (Inputs / Run / Results / History)
6. `project-context/2.build/qa.md` (AC-006 / AC-012 gaps, live timing)
7. `project-context/2.build/security.md` (S-01, S-03, S-04)
8. `project-context/3.deliver/deploy.md` (install, env names, rollback)
9. `custsuppcrew/.env.example`, `frontend/.env.example`
10. `.cursor/templates/user-guide-template.md`
11. `aamad.config.yml` (`documentation.require_user_guide: true`)

## Assumptions

1. `setup.md` remains absent; uv/npm commands above match backend/integration practice.
2. Operator accepts local unauthenticated demo (AD-09) and the AC-006 Results gap.
3. Compose images and `docker compose up` were not executed while writing this guide.
4. Browser matrix is “current desktop browser on loopback,” not a certified support list.
5. End users of this MVP are the same people who operate the laptop stack.

## Open Questions

1. Should `@project.mgr` add `setup.md` and then point this guide at it?
2. Confirm version string `0.1.0` vs `0.1.0-mvp` on the title page.
3. Should History persist across refresh (`localStorage`) before durable FR-105/FR-106?

## Audit

- **Timestamp:** 2026-08-30T13:55:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `document-user-guide`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Read user-guide template, PRD §1–2, frontend-functional-spec §1–4, integration.md run/verify, qa.md gaps, deploy.md runbook, `.env.example` names. Wrote this file only (plus a deploy.md pointer/Audit). Did not start services or change application logic.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.

- **Timestamp:** 2026-08-30T14:00:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `document-user-guide` (idempotent re-verify)
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Re-read template headings and this file. Self-check: sections 1–7 plus Sources, Assumptions, Open Questions, Audit are present. `setup.md` still missing. No product-capability drift vs PRD/integration/deploy. Did not rewrite body. Did not start services.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.
