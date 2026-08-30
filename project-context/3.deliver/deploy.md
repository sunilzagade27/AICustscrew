# Deploy — Release readiness + deploy definition

## Summary

Phase 3 Deliver continues after a **conditional** QA/security gate. `*prepare-release` recorded version `0.1.0` and scoped gaps. This increment is **`*define-deploy` only**: SAD §5 three-service Docker Compose, runtime-aligned images, loopback host publish. No CI workflow, no completed runbook, no user guide, and **no live `docker compose up`**.

**Release version:** `0.1.0` (from `custsuppcrew/pyproject.toml` and `frontend/package.json`).

**Gate:** **Conditional pass** — QA documents MVP verification with **explicitly scoped known gaps**; security.md is present and allows local packaging if S-01 stays untracked and AD-09 / Vite LAN bind are accepted.

## Phase gate

| Input | Status |
| --- | --- |
| `project-context/2.build/qa.md` | Present. Unit 22 passed; API integration 15 passed; FE mapper 4 passed; live `*verify-flow` kickoff **complete** (287.8s). |
| `project-context/2.build/security.md` | Present. No Critical. High S-01 = do not commit nested `.env` scaffold. |
| `backend.md` / `frontend.md` / `integration.md` | Present |
| PRD / SAD | Present |
| `setup.md` | **Missing** — local run steps taken from backend.md / integration.md |
| `aamad.config.yml` `security.require_security_assessment` | true — **satisfied** by security.md |

### QA scoped known gaps (accepted for `0.1.0` local MVP)

1. AC-006 live aggregate JSON often stored as `parse_error`; Results may show specialist Key Insights and **No findings.** for other headings (`qa.md` `*verify-flow`).
2. AC-012 redact overlap on `Authorization: Bearer` (`trace_log.py`).
3. No automated browser E2E.
4. 404 error code is `INTERNAL` (SAD has no `NOT_FOUND`).

### Security conditions for this release

- Keep `custsuppcrew/src/custsuppcrew/guide_creator_flow/` **untracked**. Compose build excludes that tree via `custsuppcrew/.dockerignore`.
- Do not publish `investigate-api` or `stub-telemetry` off `127.0.0.1` on the **host**. Compose maps `127.0.0.1:8000` and `127.0.0.1:8081` only.
- Operator accepts SAD AD-09 (unauthenticated localhost) and security S-03 (Vite `host: true` applies to the **dev** Vite path; Compose UI is nginx on `127.0.0.1:3000`).

## Release notes (`0.1.0`)

Investigation-first SRE assistant MVP:

- CrewAI sequential crew: supervisor + kubernetes, logs, metrics, runbooks specialists; read-only stub telemetry on `:8081`.
- FastAPI `GET /health`, `POST /v1/investigations` (SSE / blocking JSON / `?wait=false` 202 poll), `GET /v1/investigations/{id}` on `127.0.0.1:8000`.
- Vite Critical Research UI on `:3000`: Inputs → Run (plan preview) → Results (AC-006 headings when parse succeeds); session History; stub banner; Future Work labels.
- Tests: pytest unit + API TestClient; Node FSM and snapshot-mapper tests; `npm run typecheck`.

**Not in this release:** live cluster connectors, Slack/PagerDuty, SSO, SSE UI client, Next.js App Router, durable history, AgentCore hosting, mutating tools.

## Deploy definition (`*define-deploy`)

SAD §5 smallest MVP host is **Docker Compose** (or equivalent local processes). Scaffold created; **not started**.

### Hosting target

| Service | Role | Image / start | Host publish | In-container listen | Health |
| --- | --- | --- | --- | --- | --- |
| `stubs` | Stub OpenAPI | `custsuppcrew/Dockerfile` + `uvicorn custsuppcrew.stubs.app:app --host 0.0.0.0 --port 8081` | `127.0.0.1:8081:8081` | `0.0.0.0:8081` | `GET /health` |
| `api` | FastAPI + CrewAI | same image + `uvicorn custsuppcrew.api:app --host 0.0.0.0 --port 8000` | `127.0.0.1:8000:8000` | `0.0.0.0:8000` | `GET /health` |
| `frontend` | static SPA (SAD named Next.js; implemented Vite build + nginx) | `frontend/Dockerfile` (`node:22-alpine` build, `nginx:1.27-alpine`) | `127.0.0.1:3000:80` | `80` | HTTP 200 `/` |

**Why in-container `0.0.0.0`:** Docker publishes the container port to the host. The application `run_api()` / `run_stubs()` loopback bind is unchanged for the **non-Docker** process path. Compose `CMD` overrides listen address so the compose network can reach the processes. **S-04 is enforced at the host publish**, not by changing application bind logic.

**Why browser uses `127.0.0.1:8000`:** the SPA runs in the operator browser on the host. `VITE_API_BASE_URL` is baked at image build as `http://127.0.0.1:8000`. The API container talks to stubs on the compose network as `http://stubs:8081`.

### Files created

| Path | Purpose |
| --- | --- |
| `docker-compose.yml` | Project `aicustscrew`; three services; loopback ports; healthchecks; `api` waits for healthy `stubs`; `frontend` waits for healthy `api` |
| `custsuppcrew/Dockerfile` | `python:3.12-slim`; `uv` from `ghcr.io/astral-sh/uv:latest`; `uv sync --frozen --no-dev --no-editable`; default API CMD |
| `custsuppcrew/.dockerignore` | Excludes `.venv`, `.env`, tests, and `src/custsuppcrew/guide_creator_flow` (S-01) |
| `frontend/Dockerfile` | `npm ci` + `npm run build` with `VITE_API_BASE_URL`; nginx serves `dist` |
| `frontend/nginx.conf` | SPA `try_files` → `index.html` |
| `frontend/.dockerignore` | Excludes `node_modules`, `dist`, `.env` |

### Operator start (authorized later; not executed)

1. Copy `custsuppcrew/.env.example` → `custsuppcrew/.env` and set `ANTHROPIC_API_KEY` (operator machine only).
2. From repo root: `docker compose --env-file custsuppcrew/.env up --build`.
3. Open `http://127.0.0.1:3000`. API `http://127.0.0.1:8000/health`, stubs `http://127.0.0.1:8081/health`.
4. Stop: `docker compose down`. Rollback remains “stop `api`” (SAD §5).

`docker compose config` was run to validate YAML interpolation. **`docker compose up` was not run.**

### Runtime alignment (`crewai`)

- Python 3.12 image matches `requires-python = ">=3.10,<3.14"`.
- Start command is uvicorn over the existing FastAPI apps (`custsuppcrew.api:app`, `custsuppcrew.stubs.app:app`), not AgentCore (`agent_runtime:app` on 8080 — SAD optional AWS path, out of MVP).
- Secrets: compose interpolates `ANTHROPIC_API_KEY`, `MODEL`, `LLM_TEMPERATURE` from the host / `--env-file`. No secret values in committed files.

## Required env var **names** (no values)

From `custsuppcrew/.env.example` and `frontend/.env.example`:

- `ANTHROPIC_API_KEY` — required for live LLM
- `MODEL` — optional; example `anthropic/claude-sonnet-4-20250514`
- `LLM_TEMPERATURE` — optional
- `STUB_K8S_BASE_URL`, `STUB_LOGS_BASE_URL`, `STUB_METRICS_BASE_URL`, `STUB_RUNBOOKS_BASE_URL` — compose sets `http://stubs:8081`; local processes default `http://127.0.0.1:8081`
- `VITE_API_BASE_URL` — compose build arg `http://127.0.0.1:8000`
- Unused / commented: `GATEWAY_ACCESS_TOKEN`, `DEMO_API_TOKEN`, `CREWAI_STORAGE_DIR`, `OPENAI_API_KEY`

## Access control (policy)

- Local demo: unauthenticated (AD-09). Least privilege: GET-only tools; single investigation per API process.
- Secrets: operator `.env` only; never commit values. Nested `guide_creator_flow/.env` must stay out of git (S-01). Image build excludes that directory.
- Host publish is loopback-only so unauthenticated LLM spend (S-04) stays on localhost unless the operator changes port mappings.
- Enterprise IAM/SSO/network segmentation: Future Work (PRD FR-207).

## Rollback (preview)

Stop the `api` service (`docker compose stop api` or stop `investigate-api`). IR remains on existing PagerDuty/Slack (SAD). No cluster mutation in MVP, so there is no agent-applied cluster rollback.

## Future Work (ops)

CI lint/test/build, `pip-audit` in pipeline, monitoring/APM, autoscaling, multi-region, AgentCore Runtime, pin `uv` image digest (compose currently uses `uv:latest`), optional `DEMO_API_TOKEN` before any non-loopback API.

## Next Deliver commands

1. `@devops.eng *configure-cicd` — lint, test, and build only; no live deploy.
2. `@devops.eng *document-deploy` — complete runbook (env matrix, access, rollback).
3. `@devops.eng *document-user-guide` — `user-guide.md` (config `documentation.require_user_guide: true`).

**Live deploy authorization:** not requested; not executed. Compose stack was validated with `docker compose config` only.

## Diagnostic

None blocking local packaging. `setup.md` missing is a documentation gap, not a QA-gate halt.

## Sources

1. `project-context/2.build/qa.md`
2. `project-context/2.build/security.md`
3. `project-context/2.build/backend.md`
4. `project-context/2.build/frontend.md`
5. `project-context/2.build/integration.md`
6. `project-context/1.define/prd.md`
7. `project-context/1.define/sad.md` §5 DevOps & Deployment
8. `aamad.config.yml`
9. `.cursor/agents/devops-eng.md` (`*prepare-release`, `*define-deploy`)
10. `custsuppcrew/.env.example`, `frontend/.env.example`
11. `.cursor/rules/adapter-crewai.mdc`, `.cursor/rules/delivery-workflow.mdc`

## Assumptions

1. Operator accepts QA AC-006/AC-012 gaps and security S-03/S-04 for **local** `0.1.0`.
2. Vite on `:3000` is the MVP UI (SAD AD-05 Next.js deferred). Compose serves the Vite production build via nginx, still on host port 3000.
3. Hosting for this increment is developer-laptop Compose with loopback publish. Cloud / AgentCore remains Future Work.
4. `setup.md` absence is acceptable; runbook will cite integration.md and this compose definition.
5. No operator authorization for `docker compose up`, cloud provision, or production deploy.
6. In-container `0.0.0.0` plus `127.0.0.1` host publish satisfies S-04 without changing application `run_api` / `run_stubs` bind code.
7. `ghcr.io/astral-sh/uv:latest` is acceptable for MVP reproducibility; pin a digest in a later increment if required.

## Open Questions

1. Confirm version string `0.1.0` vs a dated `0.1.0-mvp` tag?
2. ~~Scaffold Compose with API/stubs on `127.0.0.1` only (security S-04)?~~ **Resolved:** host ports are `127.0.0.1` in `docker-compose.yml`.
3. Should AC-006 parse fix land before an authorized `compose up`, or ship `0.1.0` with the gap labeled?

## Halt and Report

None. Deploy definition recorded. CI/runbook/user-guide are subsequent actions. Live stack start is blocked until the operator authorizes it.

## Audit

- **Timestamp:** 2026-08-30T12:35:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `prepare-release`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Read qa.md, security.md, backend/frontend/integration, PRD, SAD §5, aamad.config.yml, `.env.example` names; wrote this file only. Did not create Docker/CI. Did not start or stop live services. Did not modify application logic.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.

- **Timestamp:** 2026-08-30T12:40:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `define-deploy`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Read SAD §5, security.md S-01/S-03/S-04, pyproject.toml, existing `*prepare-release` deploy.md. Wrote `docker-compose.yml`, `custsuppcrew/Dockerfile`, `custsuppcrew/.dockerignore`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`. Validated with `docker compose config` (exit 0; host_ip `127.0.0.1` on 8000/8081/3000). Did not run `docker compose up` or `build`. Did not modify application or agent business logic.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.
