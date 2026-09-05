# Deploy — Release readiness, deploy definition, CI, runbook

## Summary

Phase 3 Deliver continues after a **conditional** QA/security gate. `*prepare-release` recorded version `0.1.0`. `*define-deploy` added loopback Compose. `*configure-cicd` added lint/test/build CI. `*document-deploy` added the operator runbook. This increment is **`*document-user-guide`**: `project-context/3.deliver/user-guide.md`. **No live deploy** and **no `docker compose up`** in this session.

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

## CI scaffolding (`*configure-cicd`)

SAD §5: lint, test, and build only. No deploy job. Workflow does not use repository secrets.

| Item | Value |
| --- | --- |
| File | `.github/workflows/ci.yml` |
| Triggers | `push` to `main`; all `pull_request` |
| Permissions | `contents: read` |
| Jobs | `backend` and `frontend` (parallel) |

### Backend job (`custsuppcrew`, Python 3.12, `uv`)

| Stage | Command |
| --- | --- |
| Install | `uv sync --frozen --group dev` |
| Lint | `python -m compileall` on `src` and `tests` (excludes `guide_creator_flow`) |
| Test | `pytest` on `tests/test_unit_logic.py`, `tests/test_stubs_and_tools.py`, `tests/test_api.py` (QA unit + API suites; no LLM kickoff) |
| Audit | `uv export` + `uvx pip-audit` on prod lock |

`ruff` is not in `uv.lock`. Adding it would need a style baseline from `@backend.eng`. `compileall` is the MVP syntax lint.

`pip-audit` ignore list (CrewAI transitive `chromadb 1.1.1`, no fix version in the current lock): `PYSEC-2026-311`, `CVE-2026-45830`, `CVE-2026-45833`, `CVE-2026-45831`. New findings fail the job.

### Frontend job (`frontend`, Node 22)

| Stage | Command |
| --- | --- |
| Install | `npm ci` |
| Lint / typecheck | `npm run typecheck` (`tsc -b --noEmit`). No ESLint in `package.json`. |
| Test | `npm run test:unit` and `npm run test:integration` |
| Build | `npm run build` with `VITE_API_BASE_URL=http://127.0.0.1:8000` |
| Audit | `npm audit --audit-level=high` |

### Not in CI

- Live `docker compose up` or image push
- Browser E2E
- `ANTHROPIC_API_KEY` or any secret
- Promotion to a host

## Runbook (`*document-deploy`)

Operator procedures for the **local** `0.1.0` MVP. Hosting target is a developer laptop (or single small VM) running SAD §5 three services. Cloud, AgentCore, and any non-loopback bind are out of scope.

### Hosting

| Mode | When to use | UI | API | Stubs |
| --- | --- | --- | --- | --- |
| **Compose** (SAD default) | Packaged local stack | `http://127.0.0.1:3000` (nginx) | `127.0.0.1:8000` | `127.0.0.1:8081` |
| **Local processes** (equivalent) | Day-to-day Build/QA | `http://127.0.0.1:3000` (Vite `npm run dev`) | `investigate-api` → `127.0.0.1:8000` | `stub-telemetry` → `127.0.0.1:8081` |

| Check | URL |
| --- | --- |
| Frontend | `GET http://127.0.0.1:3000/` → HTTP 200 |
| API | `GET http://127.0.0.1:8000/health` |
| Stubs | `GET http://127.0.0.1:8081/health` |

Do not change Compose host mappings from `127.0.0.1`. Do not start `run_api` / `run_stubs` with a non-loopback bind.

### Environment variable matrix (names only)

Copy `custsuppcrew/.env.example` → `custsuppcrew/.env` on the operator machine. Never commit `.env`. Never paste values into this artifact.

| Name | Required | Consumed by | Compose | Local processes | Notes |
| --- | --- | --- | --- | --- | --- |
| `ANTHROPIC_API_KEY` | Yes for a live LLM kickoff | `api` | `--env-file` interpolation | dotenv / shell | Empty key → `LLM_UNAVAILABLE` on kickoff. Health does not need it. |
| `MODEL` | No | `api` | default `anthropic/claude-sonnet-4-20250514` | same default in `.env.example` | |
| `LLM_TEMPERATURE` | No | `api` | default `0.1` | same | Ignored for gpt-5 / o-series (backend.md). |
| `STUB_K8S_BASE_URL` | No | `api` tools | **set** `http://stubs:8081` | default `http://127.0.0.1:8081` | Compose must use the service DNS name. |
| `STUB_LOGS_BASE_URL` | No | `api` tools | **set** `http://stubs:8081` | default `http://127.0.0.1:8081` | |
| `STUB_METRICS_BASE_URL` | No | `api` tools | **set** `http://stubs:8081` | default `http://127.0.0.1:8081` | |
| `STUB_RUNBOOKS_BASE_URL` | No | `api` tools | **set** `http://stubs:8081` | default `http://127.0.0.1:8081` | |
| `VITE_API_BASE_URL` | No | frontend build | Docker **build arg** `http://127.0.0.1:8000` | `frontend/.env` / `.env.example` | Browser origin talks to host loopback, not `api:8000`. |
| `OPENAI_API_KEY` | No | unused in MVP path | not passed | listed in example | Leave empty unless an operator later switches models. |
| `GATEWAY_ACCESS_TOKEN` | No | unused | not passed | commented in example | AgentCore / Gateway Future Work. |
| `DEMO_API_TOKEN` | No | unused | not passed | commented in example | SAD Open Question. Required before any non-loopback API. |
| `CREWAI_STORAGE_DIR` | No | unused | not passed | commented in example | Memory is off for MVP reproducibility. |

### Access control

| Surface | Policy |
| --- | --- |
| Chat / investigation API | Unauthenticated on localhost (SAD AD-09, PRD). Anyone who can reach `:8000` can spend LLM budget (S-04). Loopback publish is the control. |
| Stub telemetry | Read-only GET fixtures. No cluster credentials. |
| Tools | YAML allowlist; mutating name fragments rejected at bind (AC-007 / AC-009). |
| Concurrency | One in-flight investigation per API process (`429 BUSY`). |
| Secrets | Operator `.env` only. Do not `git add` `.env` or `custsuppcrew/src/custsuppcrew/guide_creator_flow/` (S-01). Compose `.dockerignore` excludes that tree. |
| CI | `contents: read`. No repository secrets. No deploy job. |
| Vite dev (`npm run dev`) | `host: true` may advertise a LAN URL (S-03). Prefer `http://127.0.0.1:3000`. Compose nginx is loopback-only. |
| Deferred | SSO / IAM / network segmentation (PRD FR-207). Optional `DEMO_API_TOKEN` before LAN/cloud expose. |

Least privilege for operators: only the person running the demo holds `ANTHROPIC_API_KEY`. Deployment credentials are not used (no cloud account in MVP).

### Manual promotion

There is no automated promotion. CI does not deploy.

1. Confirm GitHub Actions `CI` is green on the commit (`backend` + `frontend`).
2. Confirm `guide_creator_flow/` is still untracked (`git status`).
3. On the laptop: `cp custsuppcrew/.env.example custsuppcrew/.env` and set `ANTHROPIC_API_KEY` (value stays on that machine).
4. **Only after the operator authorizes a start:** from repo root, `docker compose --env-file custsuppcrew/.env up --build`.
5. Verify the three health URLs in the Hosting table.
6. Optional demo: open `http://127.0.0.1:3000`, submit a non-empty symptom (fixture text in integration.md). Expect plan then Results. AC-006 may show specialist Key Insights and **No findings.** for other headings (`qa.md`).
7. Full kickoff can take several minutes (QA live run ~288s; cap 600s). One investigation at a time.

**This runbook increment did not execute step 4.**

### Local-process start (no Compose)

From `backend.md` / `integration.md` (`setup.md` is missing):

```bash
# terminal 1
cd custsuppcrew && source .venv/bin/activate && stub-telemetry

# terminal 2
cd custsuppcrew && source .venv/bin/activate && investigate-api

# terminal 3
cd frontend && npm install && npm run dev
```

Load `custsuppcrew/.env` for the API process (operator-provided key). Open `http://127.0.0.1:3000`. Same health URLs as Compose.

### Rollback

SAD / PRD: disable the agent endpoint; incident response continues on existing PagerDuty/Slack. MVP tools do not mutate the cluster, so there is **no agent-applied cluster rollback** (AC-009).

| Situation | Action |
| --- | --- |
| Stop spending LLM / stop accepting investigations | Compose: `docker compose stop api`. Processes: stop `investigate-api`. UI and stubs can stay up; new kickoffs fail. |
| Stop the whole local stack | Compose: `docker compose down`. Processes: stop Vite, `investigate-api`, `stub-telemetry`. |
| Bad image or config after an authorized `up --build` | `docker compose down`, `git checkout` the last known-good commit, then (only if authorized) `up --build` again. |
| In-flight investigation | In-process only. Stopping `api` drops the snapshot. History in the Vite UI is session-local and is lost on refresh. |
| Cluster / customer IR | Out of band. This MVP does not page, acknowledge, or roll back workloads. |

Do not roll forward by publishing ports to `0.0.0.0` to “fix” connectivity.

### Operator checks (after an authorized start)

| Check | Expect |
| --- | --- |
| `curl -sS http://127.0.0.1:8081/health` | 200 |
| `curl -sS http://127.0.0.1:8000/health` | 200 |
| `curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/` | 200 |
| Empty `POST /v1/investigations` | 400 `VALIDATION_ERROR` (no LLM) |
| Second kickoff while one runs | 429 `BUSY` |

### Known local issues

- AC-006 `report.parse_error` on some live aggregates — UI may show specialist Key Insights only.
- AC-012 Bearer redact overlap in traces.
- Missing or invalid `ANTHROPIC_API_KEY` → kickoff `LLM_UNAVAILABLE`; health still 200.
- Port 3000/8000/8081 already bound → Compose or process start fails; stop the other stack first.
- Compose API must keep `STUB_*_BASE_URL=http://stubs:8081`. Pointing those at `127.0.0.1:8081` **inside** the `api` container will miss the stub service.

## Future Work (ops)

`ruff` / ESLint once owning personas add configs; Compose image build in CI; pin `uv` image digest; monitoring/APM; autoscaling; multi-region; AgentCore Runtime; optional `DEMO_API_TOKEN` before any non-loopback API; drop `chromadb` pip-audit ignores when CrewAI ships a fixed release; produce `setup.md` (`@project.mgr`).

## Next Deliver commands

None. Phase 3 persona actions are complete (`prepare-release`, `define-deploy`, `configure-cicd`, `document-deploy`, `document-user-guide`). User guide: `project-context/3.deliver/user-guide.md`.

**Live deploy authorization:** not requested; not executed. Compose was validated with `docker compose config` only. CI config exists; this session did not start workflows or containers.

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
9. `.cursor/agents/devops-eng.md` (`*prepare-release`, `*define-deploy`, `*configure-cicd`, `*document-deploy`, `*document-user-guide`)
10. `custsuppcrew/.env.example`, `frontend/.env.example`
11. `.cursor/rules/adapter-crewai.mdc`, `.cursor/rules/delivery-workflow.mdc`

## Assumptions

1. Operator accepts QA AC-006/AC-012 gaps and security S-03/S-04 for **local** `0.1.0`.
2. Vite on `:3000` is the MVP UI (SAD AD-05 Next.js deferred). Compose serves the Vite production build via nginx, still on host port 3000.
3. Hosting for this increment is developer-laptop Compose with loopback publish. Cloud / AgentCore remains Future Work.
4. `setup.md` absence is acceptable; this runbook cites `backend.md` / `integration.md` and the compose definition.
5. No operator authorization for `docker compose up`, cloud provision, or production deploy. Assumed host: developer laptop; ports `127.0.0.1:3000` / `:8000` / `:8081`; health `GET /` and `GET /health` as in Hosting.
6. In-container `0.0.0.0` plus `127.0.0.1` host publish satisfies S-04 without changing application `run_api` / `run_stubs` bind code.
7. `ghcr.io/astral-sh/uv:latest` is acceptable for MVP reproducibility; pin a digest in a later increment if required.
8. Frontend has no ESLint script; `npm run typecheck` is the lint+type stage. Python has no `ruff` lock entry; `compileall` is the lint stage.
9. Four `chromadb` pip-audit IDs are ignored until an upstream fix; `@security.eng` can require them to be gating later.

## Open Questions

1. Confirm version string `0.1.0` vs a dated `0.1.0-mvp` tag?
2. ~~Scaffold Compose with API/stubs on `127.0.0.1` only (security S-04)?~~ **Resolved:** host ports are `127.0.0.1` in `docker-compose.yml`.
3. Should AC-006 parse fix land before an authorized `compose up`, or ship `0.1.0` with the gap labeled?
4. ~~Add `pip-audit` / `npm audit` to CI?~~ **Resolved:** both run in `.github/workflows/ci.yml`. `chromadb` IDs listed above are ignored.

## Halt and Report

None. User guide recorded. Live stack start and any deploy job remain blocked until the operator authorizes them.

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

- **Timestamp:** 2026-08-30T13:45:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `configure-cicd`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Read SAD §5 CI/CD, qa.md test commands, security.md I-06 / `dependency_audit`, package.json, pyproject.toml. Wrote `.github/workflows/ci.yml`. Local checks: `compileall` ok; `npm audit` 0; `uv export` ok; `uvx pip-audit` reported four unfixed `chromadb` findings (IDs recorded, no exploit detail). Did not push a workflow run. Did not add a deploy job. Did not modify application or agent business logic.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.

- **Timestamp:** 2026-08-30T13:50:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `document-deploy`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Read SAD §5 rollback/hosting, PRD FR-207 / availability, security AD-09/S-01/S-03/S-04, `.env.example` names, integration.md local run, existing deploy.md. Expanded runbook sections only. Did not run `docker compose up`. Did not modify application or agent business logic.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.

- **Timestamp:** 2026-08-30T13:55:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `document-user-guide`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Read `.cursor/templates/user-guide-template.md`, PRD, frontend-functional-spec, integration.md, qa.md, deploy.md runbook. Wrote `project-context/3.deliver/user-guide.md`. Did not start services. Did not modify application or agent business logic.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.

- **Timestamp:** 2026-08-30T14:00:00-04:00
- **Persona id:** `devops-eng`
- **Action:** `document-user-guide` (idempotent re-verify)
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`)
- **Prompt Trace:** Omitted. No production-facing model execution; no secret values copied into this artifact.
- **Tooling:** Confirmed `user-guide.md` still satisfies the template (sections 1–7 + provenance). No rewrite. `setup.md` still absent.
- **Prohibited actions:** No live infrastructure, no secret values, no FE/BE code changes.
