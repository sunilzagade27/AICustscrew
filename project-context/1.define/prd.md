# Product Requirements Document: Multi-Agent SRE Incident-Response Assistant

## Input Requirements

**Deep Research Report / MRD**: `project-context/1.define/mrd.md` (authoritative; complete as of 2026-08-13).

**System Description** (optional): **Not present.** `project-context/1.define/system-description.md` was not elicited (`*elicit-requirements` was not run). This PRD does not invent stakeholder answers. Gaps are recorded under Assumptions and Open Questions.

**System Concept**: Investigation-first multi-agent SRE assistant for production incidents in distributed systems. A supervisor plus specialists (Kubernetes, logs, metrics, runbooks) correlates stubbed telemetry and runbooks, produces a cited investigation report, and never mutates a cluster in MVP. Human approval is required for any mutating action if such actions appear later.

**Selected Runtime**: `crewai` (resolved default: `AAMAD_TARGET_RUNTIME` unset; `aamad.config.yml` `runtime.target: crewai`). Amazon Bedrock AgentCore is an optional AWS host/MCP path, **not** an `AAMAD_TARGET_RUNTIME` value.

---

## PRD Structure

### 1. Executive Summary

**Problem Statement** (Research-backed when MRD exists):

* **Specific customer or operator problem**: During production incidents, on-call SREs, platform engineers, and engineering managers who own error budgets must rapidly correlate logs, metrics, Kubernetes/cluster events, and runbooks. Traditional monitoring tools return raw data without cross-system synthesis. Natural-language questions such as “Why are the payment-service pods crash looping?” are the surface buyers already understand (MRD Executive Summary; MRD Dim. 1 insight 3; AWS AgentCore SRE article as cited in MRD).
* **Quantified impact and pain points**: Unplanned incidents are a material financial and human cost. PagerDuty’s 2026 State of AI-First Operations (n=1,000) found 68% of organizations lose more than $300,000 per hour during IT incidents, 34% lose at least $500,000 per hour, and 8% lose more than $1 million per hour; 42% report developer burnout as a disruption impact; 59% already incorporate AI into operational workflows. Adjacent per-minute downtime recaps (Splunk/Cisco, EMA/BigPanda) are directional and not interchangeable with the PagerDuty survey. AWS’s reference architecture claims initial investigations that previously took 30–45 minutes can complete in 5–10 minutes (vendor/blog claim; not independently audited) (MRD Dim. 1 data points).
* **Target market or user population scope**: Beachhead is platform/SRE teams at cloud-native SaaS (Kubernetes + microservices) who already have Grafana/Prometheus or CloudWatch plus PagerDuty, and who cannot standardize on Datadog or Azure (MRD Critical Decision Points — Market Positioning). Commercial vs internal-only intent is **not elicited**; MRD assumed commercial/market-facing. Treat GTM as directional until that question is closed.

**Solution Overview** (Evidence-based):

* **Multi-agent system approach and unique value proposition**: A **portable supervisor/specialist SRE crew** with MCP-shaped, read-only tools, mandatory source citations, and a hard separation of investigation vs remediation. Default Build runtime is CrewAI (`crewai`). The product is investigation-first: it plans, fans out to specialists, and returns a cited report a human can verify. It is not an on-call scheduler, not a monitoring platform, and not an AWS-only copilot (MRD Executive Summary Recommended Approach; Dim. 5).
* **Key differentiators vs alternatives**: (1) explicit human-in-the-loop (HITL) for any mutating action; (2) source-cited findings SREs can verify; (3) adapter choice (`crewai` / `claude-agent-sdk` / `cursor-sdk`) with AgentCore as an optional AWS deploy path; (4) multi-cloud / multi-tool correlation rather than lock-in to one observability vendor. Do **not** compete as a hyperscaler-native control-plane copilot (Azure SRE Agent, Datadog Bits Investigation, AWS-only AgentCore samples) and do **not** try to beat those products on first-party telemetry at MVP (MRD Recommended Approach; operator constraint).
* **Expected business or operational outcomes and success metrics**: Reduce **time-to-context** (minutes to a cited hypothesis), not replace PagerDuty or Datadog. MVP success is a fixture-driven investigation that shows a plan, specialist findings with source IDs, and human-owned next steps. Live MTTR reduction on customer production is post-MVP (MRD Dim. 1 implications; Dim. 3 implications).

**Strategic Rationale**:

* **Why multi-agent architecture is optimal for this problem**: Incident investigation is a parallel correlation problem (cluster state, logs, metrics, runbooks) under time pressure. The AWS Bedrock AgentCore SRE article documents a proven supervisor that writes an investigation plan, routes to four specialists, and aggregates a cited report. That mapping is the default unless elicitation changes it. A single generic chat agent cannot own tool contracts, source attribution, and specialist isolation as cleanly (MRD Dim. 2 insight 1).
* **Business case / ROI or operational value**: Lead with incident-cost (PagerDuty primary survey) and investigation-time (AWS claim as directional), not a single TAM number. Analyst AIOps/observability sizes conflict (~$11B–$33B AIOps; ~$21B APM/observability; $6.8B SRE platforms in 2025) and are non-reconcilable (MRD Dim. 1 implications; MRD Conflicting information).
* **Market timing and competitive positioning**: 2026 buying motion is shifting from alerting to AI-assisted investigation. Amazon published a complete, copyable architecture, which validates demand and compresses novelty. Differentiation must be portability, HITL policy, and contract-stable stub-to-real tools—not the agent topology itself (MRD Dim. 1 competitive implication).

---

### 2. Market Context & User Analysis

**Target Market / Users** (From Research or System Description):

* **Primary user personas with detailed characteristics** (from MRD; Alice/Carol names are AWS sample personas, not elicited customers):
  * **On-call SRE / platform engineer (primary MVP user)**: Interrupt-driven. Paged, needs context before or while opening dashboards, pastes an alert or types a symptom in natural language, needs a plan, live specialist updates, cited findings, severity hints, and next steps. Will not accept uncited RCA. Owns `kubectl`/change execution themselves in MVP.
  * **Engineering manager / error-budget owner (secondary)**: Cares about blast radius, customer impact, and escalation timing. AWS “Carol” executive-style reporting is **deferred** (MRD Dim. 3; Open Question 8).
  * **Incident commander (human)**: Severity declaration, customer comms, and production mutation remain human. The assistant does not take the commander role (MRD Dim. 3 insight 4).
* **Market segment size and growth projections**: Adjacent markets are large but figures conflict by category definition. Do not use a single TAM in planning. Directional: AIOps 2025–2026 estimates roughly $11B–$33B; Gartner-linked APM/observability ~$21B in 2026; Dataintelo SRE platforms $6.8B (2025) → $18.4B (2034), 11.7% CAGR; SRE practice adoption 48% of enterprises in 2025 vs 34% in 2023 (Mordor, as cited in MRD). Business case core remains PagerDuty hourly-loss survey + investigation-time, not TAM.
* **Geographic focus and expansion opportunities**: Not elicited. MRD sources are global vendor/analyst publications (US-centric hyperscaler and incident-management vendors). No geo lock for MVP. Financial-services / DORA extra-territorial requirements are **not** in scope unless a first customer is confirmed (MRD Open Question 7).

**User Needs Analysis**:

* **Critical pain points and unmet needs**: Cross-source synthesis under time pressure; dashboard sprawl and alert fatigue; distrust of uncited LLM output; fear that agents will make the outage worse (Oct 2025 AWS us-east-1 illustrated automation/retry storms as failure amplifiers) (MRD Dim. 1 insight 3; Dim. 3 insight 5; Dim. 4 insight 5).
* **User journey mapping and interaction patterns**:
  1. Interrupt: page/alert or observed symptom.
  2. Intake: first chat message is an alert paste or natural-language symptom (not a blank “how can I help” requirement).
  3. Plan: numbered investigation steps, complexity, agents involved, auto-execute flag for **read** tools only — shown before aggregation (AWS pattern).
  4. Investigate: specialists query stub (MVP) or live (post-MVP) APIs; streaming or stepwise specialist updates.
  5. Report: cited Key Insights, Next Steps, Critical Alerts, Troubleshooting Steps; remediation as instructed `kubectl`/playbook steps, not executed.
  6. Human action: operator verifies citations, decides severity/comms/mutation.
  7. Post-incident learning: deferred (PagerDuty notes 48% cite post-incident learning as a resilience driver; not MVP).
* **Adoption barriers and success factors**: Barriers — LLM distrust, fear of unsafe automation, requirement to rip out Datadog/PagerDuty, Slack-native expectation set by incident.io/Rootly. Enablers — source attribution, stub-to-real API parity, no replacement of existing on-call or telemetry, HITL on writes (MRD Dim. 3).

**Competitive Landscape** (optional when MRD skipped):

* **Direct and indirect competitors or alternative workflows** (from MRD table): AWS Bedrock AgentCore SRE reference (blueprint, not packaged multi-cloud SaaS); Azure SRE Agent (GA; can recommend **or execute** mitigations on Azure); Datadog Bits Investigation (GA 2 Dec 2025; Datadog-locked telemetry; autonomous posture); PagerDuty Advance/AIOps (incident command, weaker deep RCA); incident.io / Rootly / FireHydrant (coordination > telemetry RCA); Dynatrace / Grafana Assistant (platform-bound copilots); Resolve AI / Ciroos and other AI-SRE startups (overlapping thesis).
* **Feature gaps and differentiation opportunities**: Portability + mandatory citations + investigation/remediation split. Weakness if the MVP only reimplements supervisor + k8s/logs/metrics/runbooks on AWS — that looks like a thinner AgentCore sample (MRD Dim. 1 competitive implication).
* **Pricing benchmarks when relevant**: Do not price against Datadog platform ACV (enterprise ACV often cited above $1M; mid-market observability $8k–$60k/year — anecdotes). Post-MVP monetization directional: per-responder seat + usage, similar to IR platforms ($12k–$25+/user/year directional from vendor pages). **No MVP price is set** (MRD Dim. 1 insight 5; Dim. 5 insight 6). Commercial vs internal remains an Open Question.

---

### 3. Technical Requirements & Architecture

**Runtime & Agent Specifications** (aligned with Selected Runtime):

* **Agent roles and responsibilities**: Five runtime agents matching the AWS reference unless elicitation changes it. Do not add Security, Database, or Network specialists in MVP (MRD Critical Decision Points; Dim. 2 implications).
  * **Supervisor**: Analyze the user query/alert, write an investigation plan, route to specialists, aggregate a cited report. Does not call mutating tools.
  * **Kubernetes specialist**: Read cluster/workload status via stub API (pods, nodes, deployments, events). No `kubectl` apply/delete/restart.
  * **Logs specialist**: Search/pattern-count application logs via stub API.
  * **Metrics specialist**: Pull performance, error, and availability trends via stub API.
  * **Runbooks specialist**: Retrieve playbooks, escalation procedures, and troubleshooting steps via stub API.
* **Collaboration patterns**: CrewAI sequential process is the MVP default for reproducibility (`adapter-crewai.mdc`). Explicit `Task.context` chaining: plan → specialist tasks → aggregate report. SAD may allow parallel specialist tasks later to address sequential latency (MRD medium risk). `allow_delegation=false` unless SAD justifies a manager pattern.
* **Task / turn orchestration and delegation boundaries**: Supervisor owns planning and synthesis. Specialists own only their tool domain. No specialist delegates to another specialist in MVP. Investigation auto-execute applies to **running the read plan**, not to mutating the cluster (MRD Dim. 2 insight 2).
* **CrewAI-style fields (runtime `crewai`)**: Each agent has `role`, `goal`, `backstory`, `tools`, `memory=False` (default for reproducibility), `allow_delegation=false`. Crew-level `max_iter <= 12`, `max_retry_limit >= 2`, `max_execution_time` tuned per investigation, `max_rpm` for budget stability. Prefer YAML `config/agents.yaml` and `config/tasks.yaml`. Temperature low for investigation determinism (MRD Dim. 2 implications; adapter-crewai).
* **Adapter vs host**: `AAMAD_TARGET_RUNTIME=crewai` constrains Phase 2 conventions. Amazon Bedrock AgentCore (Runtime, Gateway/MCP, Identity, Memory, Observability) is an **optional AWS integration/host**, compatible with CrewAI as an MCP client per AWS. Do not set `AAMAD_TARGET_RUNTIME=bedrock-agentcore` unless the adapter registry is extended (MRD Dim. 2 insight 4).

**Core Agent Definitions**:

* agent: `supervisor`
* role: "SRE investigation coordinator"
* goal: "Turn an alert or symptom into a numbered investigation plan, invoke specialists within read-only bounds, and return a cited report a human can verify"
* tools: none for cluster I/O; may use Agent-tool or task routing only as defined in SAD. No mutating tools.
* runtime notes: CrewAI sequential coordinator; `max_iter <= 12`; `memory=False`; `allow_delegation=false`; low temperature; halt if a specialist returns uncited claims

* agent: `kubernetes_specialist`
* role: "Kubernetes infrastructure investigator"
* goal: "Report pod/node/deployment/event status that is grounded in tool results; never invent cluster objects"
* tools: read-only stub (or MCP-shaped) equivalents of AWS catalog items for pod/node/deployment status and events
* runtime notes: stub HTTP/OpenAPI in MVP; refuse objects not returned by tools; no apply/restart/scale/delete

* agent: `logs_specialist`
* role: "Application log investigator"
* goal: "Search and pattern-count logs relevant to the investigation window and cite result IDs"
* tools: read-only log search / pattern APIs (stub)
* runtime notes: time-window bounded; redact secrets in log snippets before they enter the report

* agent: `metrics_specialist`
* role: "Performance metrics investigator"
* goal: "Pull latency, error, saturation, and availability trends for the named service/window and cite series IDs"
* tools: read-only performance/error/availability metric APIs (stub)
* runtime notes: numeric claims must match tool payloads; do not extrapolate beyond returned points

* agent: `runbooks_specialist`
* role: "Operational runbook investigator"
* goal: "Retrieve matching playbooks, escalation procedures, and troubleshooting steps with document/section citations"
* tools: read-only playbook / escalation / search APIs (stub; AWS lists semantic search among 21 MCP tools — subset acceptable if names stay stable)
* runtime notes: recommendations are instructions for humans; do not mark steps as executed

**Integration Requirements**:

* **Required APIs and external services (MVP)**: Four stub OpenAPI backends (Kubernetes, logs, metrics, runbooks). Tool names should stay stable relative to the AWS 21-tool catalog so live connectors can drop in later; a **subset** is acceptable (MRD Dim. 2 implications). LLM: Claude-class models as in the AWS sample (Anthropic API or Amazon Bedrock); exact model ID is a Build Audit item, not a product differentiator. Optional later: AgentCore Gateway wrapping the same OpenAPI specs as MCP tools.
* **Database and storage specifications**: MVP — no durable customer datastore required. Session transcript + source citations in-process / request-scoped. Full AgentCore-style memory namespaces (`/sre/users/{user_id}/preferences`, infrastructure knowledge, investigation history) are deferred. `CREWAI_STORAGE_DIR` only if memory is later enabled; default `memory=False`.
* **Authentication and security requirements**: No hardcoded credentials. Environment variable **names** only in artifacts and `.env.example`. Candidate names (from MRD; not all required on day one): `ANTHROPIC_API_KEY`; Bedrock invocation via IAM role (no key in repo); `GATEWAY_ACCESS_TOKEN` if/when Gateway is used. `aamad.config.yml` sets `security.require_security_assessment: true`, `forbid_committed_secrets: true`, `dependency_audit: true`. Chat MVP has no SSO/IAM requirement (deferred). Ingress JWT / Cognito as in the AWS sample is the **AWS production option**, not a Phase 2 gate.
* **Performance and scalability targets**: See §5. Local MVP is a single chat app + crew process + stub backends. Do not require AgentCore scale-to-zero to pass Build.

**Infrastructure Specifications**:

* **Cloud / hosting requirements for MVP**: Smallest credible deploy is a single service or compose stack: UI + API + CrewAI process + stub backends (MRD Dim. 4 insight 1; AAMAD Deliver default). AgentCore Runtime (ARM64 containers, FastAPI `agent_runtime:app` on port 8080 in the AWS sample, session isolation, scale-to-zero) is documented as an optional AWS path in SAD — not required to pass Build.
* **Compute and memory specifications**: Not elicited. Assumption: developer laptop / single small VM is sufficient for stubbed MVP. LLM tokens dominate cost (four specialist calls per incident) (MRD Dim. 4 insight 4).
* **Network and security architecture**: Stubs are local/private network. No live cluster credentials in MVP. Production AWS path (optional): AgentCore Identity — ingress JWT to Gateway, egress API keys to backends via credential providers (`X-API-KEY`), never in source (MRD Dim. 4 insight 3).
* **Monitoring and logging requirements**: Observe the observer. MVP: structured logs of agent, tool, latency, and errors with secret redaction under `project-context/2.build/logs` per AAMAD. Production: OpenTelemetry → CloudWatch or equivalent (MRD Dim. 4 insight 2). Prompt Trace omitted from this PRD (see Audit); runtime traces in Build must still redact secrets.

---

### 4. Functional Requirements

**Core Features** (Priority P0):

Trace: MRD Recommended Approach, Dim. 2–3 implications, Critical Decision Points. Acceptance criteria are given IDs for QA mapping (`aamad.config.yml` `testing.map_to_acceptance_criteria: true`).

* **FR-001 Incident intake (chat)**: As an on-call SRE, I can paste an alert or type a natural-language symptom as the first message so investigation starts without a blank-prompt ritual.
  * Technical constraints: AAMAD default MVP chat UI; first message = alert or symptom. Slack/Teams not required.
  * Dependencies: Frontend chat; backend kickoff payload.
  * **AC-001**: Given the chat UI is available, when the user submits a non-empty symptom or alert text, then the backend starts a CrewAI investigation and the UI shows that work has begun.
  * **AC-002**: Given an empty submission, when the user sends, then the UI does not kick off a crew and shows a validation message.

* **FR-002 Investigation plan transparency**: As an SRE, I see a numbered investigation plan (steps, agents involved, complexity or equivalent, auto-execute flag for **reads**) before or as specialists run, so I do not receive a black-box RCA.
  * Technical constraints: AWS plan UX is the pattern. Optional human approve/edit of the plan may default to auto-run **reads** (MRD Dim. 3 insight 3) — plan edit is P1.
  * **AC-003**: Given a valid intake, when the supervisor finishes planning, then the UI displays numbered steps and which specialist agents are involved before the final aggregated report.

* **FR-003 Supervisor + four specialists**: As an operator, I get findings from Kubernetes, logs, metrics, and runbooks specialists coordinated by a supervisor, matching the AWS reference split.
  * Technical constraints: Kubernetes uses a stub API (as AWS demo does). No Security/Database/Network agents.
  * **AC-004**: Given a fixture incident, when investigation completes, then the report includes distinct contributions attributable to kubernetes, logs, metrics, and runbooks specialists (or an explicit specialist error with reason), aggregated by the supervisor.

* **FR-004 Cited investigation report**: As an SRE, I receive a report with source-cited findings and sections aligned to the AWS sample: Key Insights, Next Steps, Critical Alerts, Troubleshooting Steps.
  * Technical constraints: Source attribution is MVP-mandatory. Numeric and object claims must be grounded in tool results. Refuse to invent cluster objects not returned by tools.
  * **AC-005**: Given a completed investigation, when the report is rendered, then each Key Insight that asserts cluster, log, metric, or runbook state includes a source identifier (tool name + record/id or equivalent) visible in the UI.
  * **AC-006**: Given the report schema, when output is produced, then headings Key Insights, Next Steps, Critical Alerts, and Troubleshooting Steps are present (empty section allowed only if explicitly labeled as no findings).

* **FR-005 Read-only stub APIs**: As a developer/QA, I can run the MVP against stub OpenAPI backends for Kubernetes, logs, metrics, and runbooks with no live cluster.
  * Technical constraints: Contract-stable paths/names; subset of the AWS 21-tool catalog is acceptable. No cluster mutation endpoints exposed to agents.
  * **AC-007**: Given only stub backends and documented env vars, when an investigation runs, then specialists call stubs (not a real kube-apiserver) and no mutating HTTP methods/tools are bound to agents.
  * **AC-008**: QA may use a fixture analogous to “API response times degraded 3x” **only if** stubs encode that narrative; the product must not hard-code the AWS demo story as customer truth (MRD short-term priority 4).

* **FR-006 HITL / no unsupervised remediation**: As an SRE, I am never surprised by an agent restarting, scaling, rolling back, or applying manifests. Mutating actions are out of MVP tool surface; if a mutating recommendation is shown, it is an instruction requiring human approval and is not executed by the system.
  * Technical constraints: Investigation vs remediation are separate tool classes. “Auto-execute: Yes” applies to running the investigation plan only.
  * **AC-009**: Given the MVP tool allowlist, when agents run, then no tool performs cluster mutation (restart, scale, rollback, apply, delete).
  * **AC-010**: Given a report that includes remediation, when next steps contain `kubectl` or equivalent, then they are displayed as unexecuted instructions with citations, not as completed actions.

* **FR-007 Grounding / anti-hallucination**: As an SRE, I can trust that named workloads, metrics, and runbook steps exist in tool output.
  * **AC-011**: Given a specialist tool miss (empty result), when the agent reports, then it states that the tool returned no data rather than inventing objects.

* **FR-008 Operator observability (MVP)**: As an operator, I can inspect redacted agent/tool/latency logs for a run.
  * **AC-012**: Given a completed or failed run, when logs are written, then they include agent/tool identifiers and duration or error, and do not contain secret values (API keys).

**Enhanced Features** (Priority P1):

Deferred unless justified for MVP. Not in MVP scope:

* **FR-101** Live read connectors (real Kubernetes, log store, metrics TSDB, runbook wiki) replacing stubs.
* **FR-102** Optional Amazon Bedrock AgentCore Gateway + Runtime path (MCP wrapping the same OpenAPI; session-isolated hosting).
* **FR-103** Human approve/edit of the investigation plan before specialist execution.
* **FR-104** Role-conditioned report style (AWS Alice technical vs Carol executive memory personas).
* **FR-105** Similar-incident lookup from investigation history.
* **FR-106** Session memory namespaces (user preferences, infrastructure knowledge, investigation history).

**Future Features** (Priority P2):

Explicit Future Work (MRD roadmap and Dim. 3–5):

* **FR-201** Slack/Teams-native intake and updates (table stakes for Rootly/incident.io; not MVP).
* **FR-202** PagerDuty (or equivalent) inbound page → investigation start without a chat prompt (Datadog Bits bar; not MVP).
* **FR-203** HITL-gated mutating remediation (Azure-style policy + approval); still banned until after QA of investigation-only MVP.
* **FR-204** Additional specialists: Security, Database, Network (AWS extensibility note).
* **FR-205** Autonomous investigation start on alert with no user prompt.
* **FR-206** Postmortem draft / structured post-incident learning loop.
* **FR-207** Enterprise SSO, Cognito/JWT ingress, network segmentation.
* **FR-208** Monetization (seat + usage) and commercial packaging.

---

### 5. Non-Functional Requirements

**Performance Requirements**:

* **Response time targets**: Product goal is time-to-first-cited-hypothesis, not chat-token latency alone. AWS claims 5–10 minutes for investigations that previously took 30–45 minutes (vendor/blog; not a contractual SLO). For **stubbed MVP**, assume (see Assumptions): investigation plan visible in the UI within 30 seconds of kickoff when the LLM is reachable; full cited report completes within the crew `max_execution_time` (SAD to set; suggested starting cap 10 minutes to stay inside the AWS directional band). LLM/provider outages fail fast with a Diagnostic, not a hang.
* **Throughput and concurrency specifications**: MVP is single-investigation-at-a-time per process unless SAD states otherwise. No always-on background hunter (Azure always-on AAU cost is a warning) (MRD Dim. 4 insight 4).
* **Availability and uptime requirements**: Not elicited. MVP: best-effort local/compose. Production SLO deferred. Rollback path: disable the agent endpoint; IR continues on existing PagerDuty/Slack (MRD Dim. 4 implications).

**Security & Compliance**:

* **Data protection and privacy requirements**: Stub data is synthetic. Do not persist production telemetry in MVP. Redact secrets from Prompt Trace, UI, and `project-context/2.build/logs`. `forbid_committed_secrets: true`. Never embed secret values in this PRD or other artifacts.
* **Access control and authentication specifications**: MVP chat is local/unauthenticated unless SAD adds a simple shared-secret for the demo API (env var name only). Least-privilege tool allowlists per agent. Production identity (Cognito, JWT to Gateway, credential providers) is post-MVP / optional AWS path.
* **Regulatory compliance needs when applicable**: None scoped. DORA two-hour recovery and SOC2 are Open Questions (MRD OQ 5 and 7). Do not claim compliance.
* **Security assessment**: `security.require_security_assessment: true` in `aamad.config.yml` — `@security.eng` → `project-context/2.build/security.md` is required before Deliver unless the operator explicitly accepts the gap.

**Scalability & Reliability**:

* **Scaling triggers (MVP: document deferred approach)**: Scale-to-zero AgentCore Runtime is the AWS production option. MVP does not auto-scale. Horizontal scale deferred.
* **Fault tolerance and recovery procedures**: Per-task retry `max_retry_limit >= 2`. On specialist failure, supervisor still returns a partial cited report plus Diagnostic. On budget/context overrun: halt; do not loop. Cascading-failure incidents can overwhelm agents; timeout/`max_iter` caps are mandatory (MRD Dim. 4 insight 5; adapter-crewai Failure Policy).
* **Determinism**: Low temperature; `memory=False`; fixture-based QA. Do not treat LLM RCA ranking as bit-identical across providers.

---

### 6. User Experience Design

**Interface Requirements**:

* **User interaction patterns**: Interrupt-driven chat: prompt box + streaming or stepwise plan + per-agent findings + cited next steps (MRD Dim. 3 implications). First message may be an alert paste. Mark Future Work visibly in UI for Slack, PagerDuty inbound, executive persona, and auto-remediation.
* **Web / mobile platform specifications**: Web chat MVP only. Mobile/Slack-from-phone (Datadog Bits “context before laptop”) is future work. Honor `aamad.config.yml` UI preferences: `theme: system`, `visual_style: minimal`, `prefer_modals: false` (use inline panels/stream, not modal-heavy HITL).
* **Accessibility and usability standards**: Not elicited. Assumption: keyboard-usable chat, readable citations, no color-only severity. WCAG target not specified — Open Question.

**Agent Interaction Design**:

* **Human-agent communication patterns**: Show the plan; show specialist attribution; keep the human as incident commander. Language: operational, cited, no marketing filler. AWS CLI example (`sre-agent --prompt "API response times have degraded 3x in the last hour"`) is a UX mock, not a required CLI in MVP (chat is sufficient).
* **Feedback and error handling approaches**: Loading/in-progress per specialist; partial report on specialist failure; clear message when stubs are in use (so operators do not mistake demo data for production). Empty tool results → “no data from {tool}”, not guessed RCA.
* **Transparency and explainability features**: Mandatory source IDs; numbered plan; unexecuted remediation steps labeled as recommendations. Do not hide which specialist produced which finding.

---

### 7. Success Metrics & KPIs

**Business / Operational Metrics**:

* Time-to-first-cited-hypothesis (fixture clock, not live prod MTTR).
* Directional north star (post-MVP, measured vs baseline): investigation-time compression toward the AWS 30–45 → 5–10 minute claim — **do not publish as a guaranteed SLO**.
* Do not use TAM or “beat Datadog Bits 90% faster” as an MVP KPI (vendor claims; MRD conflicting information).

**Technical Metrics**:

* **AC mapping**: unit + integration tests required (`aamad.config.yml`); tests map to AC-001–AC-012.
* **% findings with source IDs**: MVP target 100% of state-asserting insights (AC-005).
* **Hallucinated-object rate on fixtures**: 0 invented cluster objects (AC-011).
* **Mutating-tool invocations**: 0 in MVP (AC-009).
* **Crew completion**: fixture investigation completes within `max_execution_time` without exceeding `max_iter` of 12.
* **Cost**: LLM tokens per fixture run recorded in Build/QA logs; no live multi-cloud telemetry required for MVP verification (MRD Resource Requirements).

**User Experience Metrics**:

* Task completion: user can go from pasted symptom to cited next steps without leaving the chat (fixture).
* User override rate: N/A until plan-edit (P1) exists; record as future metric.
* Satisfaction: not elicited; no CSAT instrument in MVP.
* Time-to-value: first cited plan visible without Slack or PagerDuty integration.

---

### 8. Implementation Strategy

**Development Phases**:

* **Phase 1 (Define)**: MRD complete. This PRD. System description **not** elicited — architect must treat Open Questions as unresolved rather than implied requirements. Next: `@product-mgr` `*create-stories` then `@system.arch` `*create-sad` / SFS.
* **Phase 2 (Build)**: `@project.mgr` setup (Python + CrewAI per config) → `@frontend.eng` / `@backend.eng` in parallel after setup → `@integration.eng` → `@qa.eng` → `@security.eng` (required by config). Honor adapter-crewai: YAML agents/tasks, sequential process, least-privilege tools. Language preference: Python (`aamad.config.yml`).
* **Phase 3 (Deliver)**: `@devops.eng` after `qa.md` exists; `security.md` preferred/required by config. CI lint/test/build only; no live deploy without operator authorization. User guide required (`documentation.require_user_guide: true`).

**Resource Requirements**:

* One FE chat, one BE crew, four stub OpenAPI backends, tests mapped to AC-* IDs (MRD Resource Requirements).
* Timeline: standard AAMAD MVP (Define → Build → Deliver). AgentCore production packaging is post-MVP unless SAD selects AWS as hosting target.
* Budget: LLM spend during QA with fixtures; no live cluster credentials.
* Coding standards preference: type checking on; max 400 lines/file (`aamad.config.yml`) — Build personas honor unless SAD conflicts.

**Risk Mitigation**:

| Risk (from MRD) | PRD mitigation |
| --- | --- |
| Ungrounded RCA / hallucinated kubectl | FR-004, FR-007; QA fixtures; refuse missing tool objects |
| Unsafe automation | FR-006; no mutating tools in MVP; Oct 2025 AWS outage as cautionary context |
| Competing on hyperscaler-native telemetry | Positioning: portability + HITL; AgentCore as ally/deploy path |
| Secret leakage in traces | Env names only; redaction; security.md before Deliver |
| Stub-demo gap | Contract-stable APIs (FR-005); do not hard-code AWS narrative |
| CrewAI sequential latency | Caps on iter/time; SAD may parallelize specialists later |
| AgentCore not in adapter registry | Not an `AAMAD_TARGET_RUNTIME`; optional host only |
| Analyst TAM misuse | KPIs use investigation-time and citation rate, not TAM |

Go/No-Go (from MRD, adopted as product policy): **Go** if investigation-first MVP (stubs + citations + HITL), CrewAI default, no live production mutation. **No-go** if v1 must autonomously remediate customer clusters or out-feature Datadog Bits / Azure SRE Agent on first-party telemetry.

---

### 9. Launch & Go-to-Market Strategy

Commercial vs internal-only is **not elicited** (MRD Open Question 5). The following is **directional from MRD** for a commercial beachhead and is **N/A if the operator later confirms an internal-only tool**.

* **Beachhead**: Platform/SRE teams at cloud-native SaaS (Kubernetes + microservices) with Grafana/Prometheus or CloudWatch plus PagerDuty, who cannot standardize on Datadog or Azure.
* **Message**: “Cited investigation in minutes, you still own the change.”
* **Anti-positioning**: Not a monitoring platform; not an on-call scheduler; not an AWS-only copilot; not “the AWS SRE agent.” Claim a **multi-runtime SRE investigation assistant** that can use AgentCore when the customer is on AWS.
* **Channel for MVP launch**: Local/compose demo + chat UI. No Slack marketplace, no paid SKU, no sales motion in Phase 3.
* **Partnerships (post-MVP)**: PagerDuty/incident.io for intake; Grafana/Datadog/CloudWatch as data sources; MCP catalogs; optional AWS path via AgentCore samples rather than competing with them.
* **Pricing**: Unset. Do not price against Datadog ACV. Seat + usage is a post-MVP hypothesis only.

---

## Quality Assurance Checklist

- [x] Requirements traceable to MRD, system description, or recorded Assumptions (system description absent; gap recorded)
- [x] Technical specifications feasible with the selected runtime adapter (`crewai`)
- [x] Success metrics aligned with stated objectives (time-to-cited-hypothesis, citation completeness, zero mutations)
- [x] MVP vs Future Work boundaries explicit (P0 vs P1 vs P2)
- [x] Market sections populated from MRD (MRD was not skipped)

---

## Sources

1. `project-context/1.define/mrd.md` — authoritative market, competitive, architecture-pattern, UX, and risk input for this PRD (created 2026-08-13, action `create-mrd`).
2. Amit Arora and Dheeraj Oruganty, “Build multi-agent site reliability engineering assistants with Amazon Bedrock AgentCore,” AWS Machine Learning Blog — **primary technical pattern** as already incorporated in the MRD, not re-fetched for this PRD. https://aws.amazon.com/blogs/machine-learning/build-multi-agent-site-reliability-engineering-assistants-with-amazon-bedrock-agentcore/
3. `.cursor/templates/prd-template.md` — required headings.
4. `.cursor/agents/product-mgr.md` — persona contract (outputs limited to `project-context/1.define/`).
5. `aamad.config.yml` — preferences: `runtime.target: crewai`, Python, UI (system/minimal, no modals), `security.require_security_assessment: true`, unit+integration tests mapped to AC, user guide required.
6. `.cursor/rules/adapter-registry.mdc`, `.cursor/rules/adapter-crewai.mdc`, `.cursor/rules/aamad-core.mdc` — runtime resolution and CrewAI MVP controls.
7. `.cursor/templates/system-description-template.md` — consulted to document the missing elicitation artifact; no `system-description.md` existed to ingest.
8. Operator task for `*create-prd` (2026-08-13): investigation-first MVP, supervisor+specialists, cited reports, HITL for mutating actions, `crewai` default, AgentCore not an AAMAD runtime, stub APIs, no cluster mutation, do not beat Azure SRE Agent / Datadog Bits on first-party telemetry.

Market figures, competitor capabilities, and AWS investigation-time claims in this PRD are copied from the MRD with the same caveats (survey vs modeled costs; vendor-reported speedups; non-reconcilable TAM). This PRD does not add new market facts.

---

## Assumptions

1. **Missing system description**: `*elicit-requirements` was not run; `system-description.md` does not exist. Product concept, MVP boundaries, and constraints in the operator `*create-prd` task plus MRD are used instead of invented stakeholder answers (telemetry vendor lock, SSO, SLO, pricing, DORA, accessibility target, geo).
2. **MRD remains in force**: MRD assumed commercial/market-facing intent. If the operator later declares an internal-only tool, §9 GTM is N/A and this assumption should be revised; the MRD skip rationale would then belong here.
3. **Runtime**: `AAMAD_TARGET_RUNTIME` was unset at PRD authoring; resolved value is `crewai` (adapter registry default and `aamad.config.yml` `runtime.target`). Amazon Bedrock AgentCore is optional AWS hosting/MCP, not a fourth adapter.
4. **MVP scope is investigation-only**: Stub APIs; no live production connectors; no cluster mutation; Kubernetes specialist is stub-backed.
5. **Agent topology**: Supervisor + Kubernetes + Logs + Metrics + Runbooks is locked for MVP (AWS reference / MRD). No additional specialists.
6. **HITL**: Mutating remediation is explicitly banned in v1 (P2), not merely “approval-gated in v1.” Plan auto-run applies to read tools only.
7. **UI**: AAMAD chat is the MVP channel; Slack-first is future work. Config UI preferences (minimal, system theme, no modals) apply.
8. **Language**: Python is the Build preference from config; PRD does not override SAD if architecture later requires a second language.
9. **LLM**: Claude-class models as in the AWS sample; exact model, temperature, and token caps are Build Audit items. Low temperature assumed for investigation.
10. **Memory**: `memory=False` for MVP reproducibility. Alice/Carol personas deferred (P1).
11. **Stub performance targets** (30s to plan, full report within SAD `max_execution_time`, suggested 10 min cap) are planning assumptions, not measured SLOs and not MRD statistics.
12. **AWS demo metrics** (33× latency, synthetic pod names, Alice/Carol) are UX fixtures, not customer requirements or market statistics.
13. **Config vs PRD**: No conflict identified. Config does not expand MVP scope. `aamad.config.yml` is treated as preferences; this PRD remains authoritative for product scope.
14. **Patent/FTO**: Not searched (MRD). No IP claim in this PRD.
15. **Prompt Trace**: Omitted from this artifact (see Audit).

---

## Open Questions

Carried forward from MRD unless closed by this PRD. Items 3 (mutating v1) and 4 (chat vs Slack) are **closed for MVP by operator `*create-prd` constraints**; remaining items still need stakeholders or `@system.arch`.

1. Should telemetry vendors (Datadog vs Prometheus/Grafana vs CloudWatch) be locked before live connectors, or stay stub-neutral until P1? **PRD default: stub-neutral for MVP.**
2. Will the operator extend AAMAD’s adapter registry to include Bedrock AgentCore, or keep AgentCore as deploy-only? **PRD default: deploy/MCP-only; not `AAMAD_TARGET_RUNTIME`.**
3. ~~Is mutating remediation in-scope for v1 with HITL?~~ **Closed: banned until after investigation-only QA; HITL-gated mutation is P2 (FR-203).**
4. ~~Primary channel: AAMAD chat UI only, or Slack-first?~~ **Closed for MVP: AAMAD chat UI (FR-001); Slack is P2 (FR-201).**
5. Target customer: internal platform team vs external commercial product (pricing, SOC2)? **Unresolved — affects §9 and compliance NFRs.**
6. Which LLM budget and data-residency constraints apply (Bedrock vs direct Anthropic vs Azure)? **Unresolved — Build may use `ANTHROPIC_API_KEY` locally; residency is SAD/security.**
7. Does financial-services / DORA two-hour recovery apply to the first customer, adding audit-log requirements? **Unresolved — not in MVP NFRs.**
8. How should Alice/Carol memory personas map to MVP roles? **PRD default: single SRE-facing report in MVP; multi-audience is P1 (FR-104).**
9. **Elicitation gap**: Should `*elicit-requirements` still run to produce `system-description.md` (on-call workflow, HITL bar, cloud mix, accessibility, auth for the demo API), or is this PRD sufficient for `@system.arch`?
10. Accessibility target (e.g. WCAG 2.2 AA) and whether the demo API needs a shared-secret env var were not elicited.
11. Exact CrewAI `max_execution_time` and whether specialist tasks may run in parallel are SAD decisions; this PRD only requires caps and `max_iter <= 12`.

---

## Audit

- **Timestamp:** 2026-08-13T21:15:00-04:00
- **Persona id:** `product-mgr`
- **Action:** `create-prd`
- **Resolved runtime:** `crewai` (`AAMAD_TARGET_RUNTIME` unset at authoring; `aamad.config.yml` `runtime.target: crewai`). Amazon Bedrock AgentCore recorded as optional AWS hosting/MCP gateway path, not as `AAMAD_TARGET_RUNTIME`.
- **Prompt Trace:** Omitted. This artifact synthesizes an existing audited MRD and operator MVP constraints; it does not execute production-facing runtime prompts or tools against customer systems. Omission avoids duplicating long third-party article text and keeps the PRD free of secrets. Inputs were files listed in Sources only.
- **Tooling:** Read of `.cursor/agents/product-mgr.md`, `.cursor/templates/prd-template.md`, `.cursor/templates/system-description-template.md`, `project-context/1.define/mrd.md`, `aamad.config.yml`; shell check that `AAMAD_TARGET_RUNTIME` was unset. No application code, SAD, SFS, or Build/Deliver artifacts were modified. No network fetch.
- **Model / determinism:** IDE agent session; requirements copied or narrowed from MRD and operator constraints rather than newly estimated. Temperature/max_tokens of upstream vendor models used inside AWS/Datadog/Azure products are not controlled here.
- **Template self-check:** Input Requirements; Executive Summary (Problem Statement, Solution Overview, Strategic Rationale); Market Context & User Analysis (Target Market / Users, User Needs Analysis, Competitive Landscape); Technical Requirements & Architecture (Runtime & Agent Specifications, Core Agent Definitions, Integration Requirements, Infrastructure Specifications); Functional Requirements (P0, P1, P2); Non-Functional Requirements (Performance, Security & Compliance, Scalability & Reliability); User Experience Design (Interface, Agent Interaction); Success Metrics & KPIs (Business/Operational, Technical, UX); Implementation Strategy (Development Phases, Resource Requirements, Risk Mitigation); Launch & Go-to-Market Strategy; Quality Assurance Checklist; Sources; Assumptions; Open Questions; Audit — present. No heading left empty; elicitation gaps called out rather than fabricated.
- **Config honored:** Python/CrewAI preferences, security assessment required, AC-mapped tests, minimal/system UI, no committed secrets. No config vs MRD/PRD scope conflict recorded.
- **Prohibited actions:** No application implementation; no SAD/SFS/Build/Deliver edits.
