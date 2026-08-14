# Market Research Document: Multi-Agent SRE Incident-Response Assistant

## Research Query Structure

**Primary Focus**: Multi-agent Site Reliability Engineering (SRE) assistant that helps on-call engineers during production incidents in modern distributed systems—correlating logs, metrics, Kubernetes/cluster events, and runbooks; proposing root-cause hypotheses; and recommending (not autonomously applying) remediation.

**Selected Runtime** (research-time; Build-phase confirmation required): `crewai` (AAMAD default when `AAMAD_TARGET_RUNTIME` is unset). Candidate production hosting / tool-gateway path: Amazon Bedrock AgentCore. Other AAMAD adapters remain in scope: `claude-agent-sdk`, `cursor-sdk`.

**Primary technical source**: AWS Machine Learning Blog, *Build multi-agent site reliability engineering assistants with Amazon Bedrock AgentCore* (Arora & Oruganty). The article’s problem statement matches this research query: SREs must rapidly correlate logs, metrics, Kubernetes events, and runbooks during production incidents, while traditional monitoring tools provide raw data without cross-system synthesis.

---

## Executive Summary

**Market Opportunity.** Unplanned incidents are now a board-level financial risk. PagerDuty’s 2026 State of AI-First Operations survey (n=1,000 directors and senior developers across seven markets) found that 68% of organizations lose more than $300,000 per hour during IT incidents, 34% lose at least $500,000 per hour, and 8% lose more than $1 million per hour; 42% report developer burnout as a disruption impact, and 59% already incorporate AI into operational workflows. Adjacent markets that would fund this product are large and growing, but published sizes conflict because vendors define “AIOps,” “observability,” and “SRE platforms” differently: AIOps estimates for 2025–2026 range roughly from $11B to $33B; Gartner-linked APM/observability spend is cited near $21B in 2026; Dataintelo values SRE platforms at $6.8B in 2025. The investable wedge is not another dashboard. It is **investigation-time synthesis**—the gap AWS, Microsoft, Datadog, and incident-management SaaS vendors are all racing to fill.

**Technical Feasibility.** A production-credible architecture already exists as an AWS reference implementation: a supervisor agent plus four specialists (Kubernetes, logs, metrics, runbooks), 21 MCP tools exposed through Amazon Bedrock AgentCore Gateway, session-isolated AgentCore Runtime, Cognito-backed identity, three-strategy memory, and CloudWatch observability. AWS reports that initial investigations that previously took 30–45 minutes can complete in 5–10 minutes in this pattern. The same Gateway is documented as usable from LangGraph, AWS Strands, and CrewAI—so an AAMAD MVP on `crewai` can later sit on AgentCore without rewriting agent roles. Complexity is medium-high: tool contracts, source attribution, and human-in-the-loop (HITL) gates are the hard parts, not the chat UI. Demo backends in the AWS post are synthetic; real telemetry connectors are the main implementation risk.

**Recommended Approach.** Build an **investigation-first, remediation-gated** multi-agent MVP that copies the AWS supervisor/specialist split and MCP tool surface, but remains **runtime-portable and vendor-neutral**. Do not compete as a hyperscaler-native control-plane copilot (Azure SRE Agent, Datadog Bits Investigation, AWS-only AgentCore samples). Differentiate on: (1) explicit HITL for any mutating action, (2) source-cited findings SREs can verify, (3) adapter choice (`crewai` / `claude-agent-sdk` / `cursor-sdk`) with AgentCore as an optional AWS deploy path, and (4) multi-cloud / multi-tool correlation rather than lock-in to one observability vendor. Defer autonomous cluster mutation, executive-persona memory, and live production connectors to post-MVP.

---

## Detailed Findings by Dimension

### 1. Market Analysis & Opportunity Assessment

**Key Insights**

1. **Incident cost has outgrown traditional MTTR tooling.** PagerDuty (March 2026) places hourly losses in the high six to seven figures for a large share of enterprises, with secondary costs in brand (52%), recovery (50%), productivity (48%), and burnout (42%). Independent 2026 recaps of Splunk/Cisco “Hidden Costs of Downtime” cite ~$15,000 per minute cross-industry; EMA/BigPanda (2024) cited $14,056 per minute average and $23,750 for large enterprises. These figures are not interchangeable (survey vs. modeled averages; inclusion of reputation), but they agree that minutes of investigation delay are economically material.

2. **The buying motion is shifting from alerting to AI-assisted investigation.** On-call routing, escalation, and postmortem templates have commoditized among PagerDuty, incident.io, Rootly, and FireHydrant. Differentiation in 2026 is LLM-assisted timelines, similar-incident search, impact estimation, and RCA drafts. Observability vendors (Datadog Bits Investigation GA 2 Dec 2025; Dynatrace agentic operations; Grafana Assistant) and hyperscalers (Azure SRE Agent GA; AWS AgentCore SRE blueprint) are entering the same “on-call teammate” category.

3. **The unmet need is cross-source synthesis under time pressure, not more telemetry.** The AWS AgentCore SRE post states the problem directly: during production incidents SREs must correlate logs, metrics, Kubernetes events, and runbooks, while traditional monitoring leaves them to piece the story together manually. Natural-language queries such as “Why are the payment-service pods crash looping?” are the product surface buyers already understand.

4. **SRE practice is spreading, which expands the persona—not just Google-style SRE teams.** Mordor Intelligence reported SRE practices at 48% of enterprises in 2025 vs. 34% in 2023. Target buyers are on-call SREs, platform engineers, and engineering managers who own error budgets—not only Fortune 100 SRE orgs.

5. **Willingness to pay is validated by adjacent ACV and new AI-SRE funding, but this product should not assume Datadog-scale ACV at MVP.** Public APM/observability ACV anecdotes (Datadog enterprise ACV often cited above $1M; mid-market observability $8k–$60k/year) show budget exists. Specialist “AI SRE” vendors (e.g., Resolve AI Series A reported at $125M / ~$1B valuation; Ciroos $21M with claimed 90% faster incident closure) confirm a category, not a guaranteed price point for a new multi-agent MVP.

**Data Points**

| Claim | Figure | Source |
| --- | --- | --- |
| Share losing >$300k / hour in incidents | 68% | PagerDuty 2026 State of AI-First Operations (Wakefield, n=1,000) |
| Share losing ≥$500k / hour | 34% | Same |
| Share losing >$1M / hour | 8% | Same |
| Organizations using AI in digital operations | 59%; 75% of AI adopters report improved resilience vs 66% non-adopters | Same |
| Plan to increase operational-resilience budget (12 months) | 77% overall; 82% of revenue growers | Same |
| Post-incident learning as resilience driver | 48% | Same |
| Developer burnout as disruption impact | 42% | Same |
| Investigation time (AWS reference architecture claim) | 30–45 min → 5–10 min | AWS Bedrock AgentCore SRE blog |
| AIOps market (conflicting) | ~$11.16B (2025, Zylos) vs $15.96B (2025, TBRC) vs $18.95B (2026, Mordor) vs $33.19B (2025, Expert Market Research) | Analyst reports; treat as order-of-magnitude only |
| SRE platform market | $6.8B (2025) → $18.4B (2034), 11.7% CAGR | Dataintelo |
| APM/observability envelope | ~$21B (2026, Gartner-linked recap) | JustAnalytics / Gartner IT spending recaps |
| SRE practice adoption | 48% of enterprises (2025) vs 34% (2023) | Mordor Intelligence AIOps report |

**Source Citations**

- PagerDuty newsroom, 17 Mar 2026, 2026 State of AI-First Operations.
- PagerDuty, How to Reduce MTTR — 2026 Guide (repeats $300k/$500k hourly loss; cites $800k average customer-impacting incident, $4,537/min, 175 min average resolve—vendor blog, treat as directional).
- AWS ML Blog, Build multi-agent SRE assistants with Amazon Bedrock AgentCore.
- Mordor Intelligence, AIOps Market; Dataintelo, Service Reliability Engineering Platform Market; Expert Market Research / TBRC / Zylos AIOps size notes.
- Datadog Bits AI SRE GA press release, 2 Dec 2025.
- Microsoft Azure SRE Agent product page and GA notes (Mar 2026 Tech Community).

**Implications**

- Position the MVP as **time-to-context** (minutes to a cited hypothesis), not as a replacement for PagerDuty on-call or Datadog telemetry.
- Price later against incident-management seats and AIOps add-ons, not against full observability platforms.
- Flag analyst TAM figures as **non-reconcilable**; use PagerDuty’s primary survey and AWS’s investigation-time claim as the business-case core.
- Commercial viability depends on integrating with tools SREs already pay for (Slack/Teams, PagerDuty, Grafana/Prometheus, Kubernetes, runbook wikis)—not on owning the data plane.

**Competitive Landscape (feature view)**

| Player | Type | Incident-time strength | Weakness vs this concept |
| --- | --- | --- | --- |
| **AWS Bedrock AgentCore SRE assistant** (Arora/Oruganty reference) | Hyperscaler blueprint + samples | Supervisor + 4 specialists; 21 MCP tools; memory personas; source attribution; CrewAI/LangGraph/Strands compatible Gateway | Not a multi-cloud SaaS; demo APIs are synthetic; AWS-centric runtime (AgentCore, Cognito, CloudWatch); investigation-oriented, not a packaged product |
| **Azure SRE Agent** | Hyperscaler product (GA) | Always-on Azure monitoring, RCA, recommend **or execute** mitigations (restart/scale/rollback) with policy + human approval; MCP extensibility; PagerDuty/GitHub/ServiceNow | Azure-hosted applications; usage billed in Azure Agent Units; weaker story for AWS/GCP/on-prem stacks |
| **Datadog Bits Investigation** | Observability-native agent (GA 2 Dec 2025) | Autonomous investigation from the page; topology + telemetry; tested in 2,000+ customer environments; proposed code fixes | Locked to Datadog data; “autonomous” posture may conflict with regulated HITL policies |
| **PagerDuty Advance / AIOps** | Incident command incumbent | On-call, routing, 700+ integrations, postmortem drafts from Slack + change events | Weaker in-incident technical investigation vs Slack-native IR tools and observability agents |
| **incident.io, Rootly, FireHydrant** | Lifecycle IR platforms | Slack-native coordination, automation, AI postmortems, similar-incident search | Coordination > deep telemetry RCA |
| **Dynatrace Intelligence / Davis CoPilot, Grafana Assistant** | Observability copilots | Query generation, Davis RCA, PromQL/LogQL/TraceQL NL | Platform-bound |
| **Resolve AI, Ciroos, other AI-SRE startups** | Category specialists | Dedicated “AI SRE teammate” narrative and funding | Overlapping thesis; differentiation will be thin without HITL + portability story |

**Competitive implication of the AWS article:** Amazon published a **complete, copyable architecture** for exactly this product. That validates demand and simultaneously compresses novelty. A new MVP that only reimplements supervisor + k8s/logs/metrics/runbooks on AWS will look like a thinner AgentCore sample. Differentiation must be portability, HITL policy, and live (or realistically stubbed) multi-vendor tools—not the agent topology itself.

---

### 2. Technical Feasibility & Requirements Analysis

**Key Insights**

1. **Supervisor/specialist is the proven pattern for SRE investigation.** AWS specifies a supervisor that analyzes the query, writes an investigation plan, routes to specialists, and aggregates a report, plus four specialists: Kubernetes infrastructure, application logs, performance metrics, and operational runbooks. The worked example (“API response times have degraded 3x in the last hour”) sequences metrics → logs → Kubernetes and surfaces cascading failure (missing ConfigMap → CrashLoopBackOff → API 33× slower). That mapping should be the SAD/backend default unless elicitation changes it.

2. **Investigation and remediation must be separate tool classes.** In the AWS walkthrough, “Auto-execute: Yes” applies to **running the investigation plan**, not to mutating the cluster. Remediation appears as cited `kubectl` steps, ConfigMap fixes, and runbook playbooks for a human. Azure SRE Agent, by contrast, will recommend **or execute** restart/scale/rollback under guardrails. MVP must implement **read/investigate tools only**; any write tool is a post-MVP gated action.

3. **MCP is the integration contract.** AgentCore Gateway turns existing OpenAPI backends (Kubernetes, logs, metrics, runbooks) into MCP tools (21 listed, including pod/node/deployment status, log search/patterns, performance/error/availability metrics, playbooks, escalation procedures, and semantic `x_amz_bedrock_agentcore_search`). AWS states existing APIs need no rewrite—only OpenAPI specs—and that the Gateway works with LangGraph, Strands, **and CrewAI**. This is the cleanest path to keep AAMAD `crewai` while remaining deployable on AWS later.

4. **AAMAD adapters vs AgentCore are complementary, not mutually exclusive.**

   | Runtime | Role in this product | Fit |
   | --- | --- | --- |
   | `crewai` (default) | Agent/task YAML, sequential process, `Task.context` chaining | High: supervisor + specialists map 1:1 to CrewAI agents/tasks; AWS explicitly lists CrewAI as an MCP client of AgentCore Gateway |
   | `claude-agent-sdk` | Coordinator + `Agent` tool specialists, hooks, MCP | High: mirrors supervisor/specialist; strong HITL via tool allowlists |
   | `cursor-sdk` | TypeScript contract-first agents | Medium: good if MVP UI/backend is TS-first; weaker YAML-ops familiarity for SRE teams |
   | **Amazon Bedrock AgentCore** | Production **Runtime** (ARM64 containers, session isolation, scale-to-zero), **Gateway** (MCP), **Identity**, **Memory**, **Observability** | Strong **hosting/integration** candidate for AWS customers; **not** an AAMAD adapter today. Do not set `AAMAD_TARGET_RUNTIME=bedrock-agentcore` unless the registry is extended. |

5. **Memory and observability are production requirements, not v2 polish.** AgentCore Memory uses three namespaces: user preferences (`/sre/users/{user_id}/preferences`), infrastructure knowledge, and investigation history. Alice (technical SRE) vs Carol (executive) get the same findings in different report styles. AgentCore Observability (OpenTelemetry + CloudWatch) records LLM tokens/latency, MCP tool duration/success, memory ops, and end-to-end traces. MVP can stub memory as session transcript + source citations; full preference memory can wait. **Source attribution is MVP-mandatory** (AWS lists it as a first-class capability for verification and audit).

**Data Points**

- 4 specialists + 1 supervisor; 21 MCP tools after Gateway deploy (AWS blog tool listing).
- LLM options in the sample: Anthropic Claude 3.7 Sonnet via Amazon Bedrock, or Claude 4 Sonnet via Anthropic API.
- Runtime: ARM64 containers, FastAPI `agent_runtime:app` on port 8080, `opentelemetry-instrument`, IAM or OAuth invocation.
- AWS claimed investigation compression: 30–45 minutes → 5–10 minutes (vendor/blog claim; not independently audited).
- Datadog Bits: tens of thousands of investigations; 2,000+ customer environments (vendor).
- October 2025 AWS us-east-1 / DynamoDB DNS race and multi-hour control-plane congestive collapse (public post-event analyses) illustrate why single-dashboard RCA fails on cascading distributed failures.

**Source Citations**

- AWS ML Blog, Bedrock AgentCore SRE assistants (architecture, tools, memory, runtime, HITL-style outputs).
- Amazon Bedrock AgentCore samples (`awslabs` AgentCore samples; AWS blog “GitHub repository” / AgentCore Samples).
- AAMAD adapter rules: `.cursor/rules/adapter-crewai.mdc`, `adapter-claude-agent-sdk.mdc`, `adapter-cursor-sdk.mdc`, `adapter-registry.mdc`.
- Datadog Bits AI SRE GA (2 Dec 2025); Azure SRE Agent product page.
- Public analyses of the Oct 2025 AWS us-east-1 incident (Pragmatic Engineer; AWS post-event summaries cited in secondary write-ups).

**Implications**

- **MVP agent set:** Supervisor, Logs, Metrics, Runbooks; Kubernetes specialist can use a stub API (as AWS demo does).
- **MVP tools:** read-only MCP or in-process equivalents of the AWS 21-tool catalog (subset is acceptable; names should stay stable).
- **Do not auto-run kubectl** in MVP. Show commands with sources.
- **Technical risks:** hallucinated RCA without grounding; secret leakage in traces; AgentCore lock-in if memory/identity are used before an abstraction exists; synthetic-demo overfitting.
- **Infrastructure for local MVP:** single chat app + crew process; stub HTTP backends for k8s/logs/metrics/runbooks. Production AWS path: AgentCore Runtime + Gateway + Cognito + CloudWatch, documented as optional in SAD—not required to pass Build.

---

### 3. User Experience & Workflow Analysis

**Key Insights**

1. **The primary journey is interrupt-driven, not chat-first.** On-call is paged → needs context before arriving at a laptop (Datadog Bits’ explicit promise) → asks a natural-language question or pastes an alert → receives a plan, live specialist updates, cited findings, severity, and next steps. AWS’s CLI example (`sre-agent --prompt "API response times have degraded 3x in the last hour"`) and “customer interface receives alerts… returns comprehensive agent responses” both describe this loop. AAMAD’s default MVP chat UI is acceptable if the first message can be an alert or symptom, not a blank prompt.

2. **Show the investigation plan.** AWS prints numbered steps, complexity, auto-execute flag, and agents involved **before** aggregation. That is the right UX for trust: SREs will not accept a black-box RCA.

3. **HITL is role- and action-specific.** AWS personalizes *presentation* (Alice: systematic technical exposition, 15-minute escalation; Carol: business impact, 5-minute escalation) but still leaves cluster changes as instructed steps. Azure executes mitigations only with policy + approval. **MVP HITL policy:** always human-approve mutating actions; always cite sources; optional approve/edit of the investigation plan (can default to auto-run reads). Do not ship unsupervised remediation.

4. **Automation split.** Fully automate: tool fan-out, log pattern counts, metric trend pull, runbook retrieval, timeline assembly, similar-incident lookup (post-MVP). Partial: root-cause ranking, blast-radius narrative. Human: severity declaration, customer comms, production mutation, incident commander role.

5. **Adoption barriers.** Alert fatigue and dashboard sprawl (PagerDuty MTTR guide); distrust of uncited LLM output; fear of agents making the outage worse (Oct 2025 AWS outage: automation and retry storms *were* failure amplifiers). Enablers: source attribution, stub-to-real API parity, Slack-native later (table stakes for Rootly/incident.io), no requirement to rip out Datadog/PagerDuty.

**Data Points**

- AWS example impact line: API 150ms → 5000ms (33×), 75% error rate, memory 100%, CPU 95% (synthetic demo—use as UX mock, not as a market statistic).
- PagerDuty: 48% improved resilience via structured post-incident learning; successful firms more likely to demand continuous learning (83% vs 77%).
- Bits Investigation: autonomous start on alert (no prompt required)—a UX bar the MVP will not meet initially; document as future work.

**Source Citations**

- AWS AgentCore SRE blog (journey, plan UX, Alice/Carol memory, executive summary sections: Key Insights, Next Steps, Critical Alerts, Troubleshooting Steps).
- PagerDuty 2026 report (learning loop, burnout).
- Datadog Bits Investigation product/blog (autonomous on-call teammate).
- Azure SRE Agent (approval-gated execution).

**Implications**

- Chat MVP: prompt box + streaming plan + per-agent findings + cited next steps.
- Success metrics for the product (not the crew that builds it): time-to-first-cited-hypothesis, % findings with source IDs, user override rate, MTTR delta vs baseline (measure in QA with fixtures, not live prod).
- Mark Slack/Teams, PagerDuty inbound, and executive-summary personas as **future work** in UI and docs.

---

### 4. Production & Operations Requirements

**Key Insights**

1. **Smallest credible deploy is a single service, not AgentCore.** SAD/delivery rules prefer the smallest MVP host. Local/compose: UI + API + crew + stub backends. AgentCore Runtime (scale-to-zero, session isolation, IAM) is the **AWS production option**, not the Phase 2 gate.

2. **Observe the observer.** AWS instruments LLM, tool, memory, and request traces. An SRE assistant that cannot show its own traces will not be trusted. MVP: structured logs of agent/tool/latency with secret redaction (`project-context/2.build/logs` per AAMAD). Production: OTel → CloudWatch or equivalent.

3. **Security: identity on tools, never secrets in artifacts.** AgentCore Identity: ingress JWT to Gateway, egress API keys to backends via credential providers (`X-API-KEY`), no hardcoded credentials. Cognito in the sample. `.env.example` names only (`ANTHROPIC_API_KEY` / Bedrock IAM, `GATEWAY_ACCESS_TOKEN`, etc.). `security.require_security_assessment: true` in the example AAMAD config—honor if copied to `aamad.config.yml`.

4. **Cost structure.** LLM tokens per specialist (four parallel/sequential calls per incident) dominate. AgentCore Runtime scale-to-zero helps idle cost; Azure’s always-on SRE Agent baseline AAU is a warning that “always-on investigation” is expensive. Stub backends are cheap; real log/metric APIs may incur vendor egress.

5. **Operational risk.** A wrong remediation suggestion that is auto-applied is a high-severity failure mode. Keep remediation human-gated. Cascading-failure incidents (AWS Oct 2025) can overwhelm both humans and agents; document timeout/budget caps (`max_iter`, `max_execution_time` per CrewAI adapter).

**Data Points**

- AgentCore Runtime: public network mode in sample `create_agent_runtime`; ARM64 required.
- Cleanup surface in AWS sample: Gateway, targets, Memory, Runtime, local tokens/ARNs.
- Compliance drivers (secondary): EU DORA recovery expectations for financial entities appear in AIOps analyst notes as a demand driver—not verified here as a product requirement unless the PRD scopes financial-services customers.

**Source Citations**

- AWS AgentCore SRE blog (Runtime, Identity, Observability, cleanup).
- AAMAD delivery-workflow and aamad-core security rules.
- Azure SRE Agent pricing model (fixed always-on + usage AAU)—contrast with scale-to-zero AgentCore.

**Implications**

- Deliver artifact later should list env var **names** from `.env.example` only.
- Rollback: disable agent endpoint; IR continues on existing PagerDuty/Slack.
- Do not call live deploy during Deliver without operator authorization.

---

### 5. Innovation & Differentiation Analysis

**Key Insights**

1. **Unique value (defensible for an AAMAD MVP):** a **portable supervisor/specialist SRE crew** with MCP-shaped tools, mandatory citations, and **hard separation of investigation vs remediation**, runnable on CrewAI locally and optionally on AgentCore for AWS customers. Hyperscaler assistants optimize for *their* control plane.

2. **Emerging tech to adopt, not reinvent:** MCP tool gateways; supervisor-agent planning; session memory; OTel for agents; role-conditioned reporting (AWS Alice/Carol). Agentic remediation (Azure) and autonomous page-to-RCA (Datadog) are table stakes in 2026 marketing—**unsafe as MVP defaults**.

3. **Patent / IP.** No freedom-to-operate search was performed. Supervisor-agent orchestration, RAG over runbooks, and incident timeline generation are crowded. Treat IP as an open question; Apache-2.0 AAMAD licensing covers the framework, not third-party cloud APIs.

4. **Future trend:** “AI SRE teammate” consolidates into observability suites and hyperscalers. Independent products survive if they are **tool-agnostic coordinators** (the incident.io/Rootly lesson) plus **deep investigation** (the Bits/AgentCore lesson). Pure chat wrappers will not.

5. **Partnerships:** PagerDuty/incident.io for intake; Grafana/Datadog/CloudWatch as data sources; MCP catalogs; optional AWS partnership via AgentCore samples rather than competing with them.

6. **Monetization (post-MVP):** per-responder seat + usage (investigations/tokens), similar to IR platforms ($12k–$25+/user/year directional from vendor pricing pages). Do not price against Datadog platform ACV.

**Source Citations**

- AWS AgentCore SRE blog (extensibility: Security, Database, Network agents; replace stubs with real k8s/logs/metrics/runbooks).
- Datadog, Azure, Rootly/incident.io competitive pages (see Sources).
- Resolve AI / Ciroos funding mentions in 2026 observability recaps (secondary; verify if used in investor materials).

**Implications**

- Roadmap: MVP investigation crew → live read APIs → Slack + PagerDuty → gated remediation → optional AgentCore deploy.
- Explicitly **do not** claim to be “the AWS SRE agent”; claim **multi-runtime SRE investigation assistant** that can use AgentCore when the customer is on AWS.

---

## Critical Decision Points

### Go/No-Go Factors

- **Go** if stakeholders accept investigation-first MVP (stubs + citations + HITL), CrewAI as default runtime, and no live production mutation.
- **No-go / halt** if the expected product is autonomous remediation on customer clusters in v1, or if it must out-feature Datadog Bits/Azure SRE Agent on first-party telemetry at MVP.
- **Prerequisite:** operator confirms commercial (not internal-only) intent so this MRD remains in force; otherwise skip rationale belongs in PRD Assumptions.

### Technical Architecture Choices

- **Agents:** Supervisor + Logs + Metrics + Runbooks (+ Kubernetes stub). Matches AWS reference; do not add Security/Database/Network agents in MVP.
- **Runtime:** Generate MVP on `crewai` unless operator sets `AAMAD_TARGET_RUNTIME`. Document AgentCore Gateway/Runtime as an **optional AWS integration/host**, compatible with CrewAI via MCP per AWS.
- **Tools:** MCP or MCP-shaped OpenAPI; read-only in MVP.
- **LLM:** Claude-class models as in AWS sample; record model/temperature in Build Audit; keep temperature low for investigation determinism.

### Market Positioning

- **Beachhead:** Platform/SRE teams at cloud-native SaaS (Kubernetes + microservices) who already have Grafana/Prometheus or CloudWatch plus PagerDuty, and who cannot standardize on Datadog or Azure.
- **Message:** “Cited investigation in minutes, you still own the change.”
- **Anti-positioning:** Not a monitoring platform; not an on-call scheduler; not an AWS-only copilot.

### Resource Requirements

- Define remaining: `*elicit-requirements` (recommended) then PRD + stories.
- Build: one FE chat, one BE crew, stub APIs, tests mapped to AC-* IDs.
- Timeline: standard AAMAD MVP (Define → Build → Deliver); AgentCore production packaging is post-MVP unless SAD selects AWS as hosting target.
- Budget: LLM spend during QA with fixtures; no live multi-cloud telemetry required for MVP verification.

---

## Risk Assessment Matrix

### High Risk

- **Ungrounded RCA / hallucinated kubectl.** Mitigation: mandatory source attribution (AWS pattern); refuse to invent cluster objects not returned by tools; QA fixtures.
- **Unsafe automation.** Mitigation: no mutating tools in MVP; Azure-style approval if added later. Oct 2025 AWS outage shows automation can deepen incidents.
- **Competing with hyperscaler-native assistants on their turf.** Mitigation: portability + HITL positioning; treat AgentCore as ally/deploy path.
- **Secret leakage in Prompt Trace / CloudWatch.** Mitigation: redact; env vars only; security.md before Deliver if config requires it.

### Medium Risk

- **Analyst TAM contradiction** misleading business case. Mitigation: lead with PagerDuty primary survey + investigation-time value, not a single TAM number.
- **Stub-demo gap** (AWS itself uses synthetic backends). Mitigation: contract-stable APIs so real connectors drop in; integration tests against stubs.
- **CrewAI sequential latency** vs parallel specialist fan-out. Mitigation: SAD may allow parallel specialist tasks; cap `max_iter` / time.
- **AgentCore not in AAMAD adapter registry.** Mitigation: do not silently invent `AAMAD_TARGET_RUNTIME=bedrock-agentcore`; record as Open Question for architect.

### Low Risk

- Executive-persona memory (Carol) deferred.
- Slack-native UX deferred (competitors already own it).
- Patent thicket for generic multi-agent orchestration (monitor, do not block MVP).

---

## Actionable Recommendations

### Immediate Next Steps (48 hours)

1. Operator: confirm commercial vs internal tool (keeps this MRD vs skip).
2. Run `@product-mgr` `*elicit-requirements` for system-description.md (specialized SRE workflow: which telemetry, HITL bar, cloud mix).
3. Capture `AAMAD_TARGET_RUNTIME` if not `crewai`; do not treat AgentCore as the AAMAD runtime id.
4. Read the AWS post + AgentCore samples as the architecture baseline for `@system.arch`.

### Short-term Priorities (30 days)

1. `*create-prd` and `*create-stories` from this MRD + elicitation.
2. SAD: supervisor/specialist view, read-only tool policy, optional AgentCore deploy diagram.
3. MVP: chat + CrewAI crew + four stub OpenAPI backends + cited report schema matching AWS sections (Key Insights, Next Steps, Critical Alerts, Troubleshooting Steps).
4. QA: fixture incident (“API 3× slower”) with expected ConfigMap/pod-crash correlation **only if** stubs encode it—do not hard-code AWS demo narrative as real customer truth.

### Long-term Strategy (6–12 months)

1. Replace stubs with real k8s, log, metrics, runbook systems.
2. Optional AgentCore Gateway + Runtime path for AWS-hosted customers; keep adapters for non-AWS.
3. PagerDuty/Slack intake; similar-incident memory; gated remediation.
4. Reassess differentiation quarterly against Bits, Azure SRE Agent, and AgentCore sample updates.

---

## Sources

1. Amit Arora and Dheeraj Oruganty, “Build multi-agent site reliability engineering assistants with Amazon Bedrock AgentCore,” AWS Machine Learning Blog. https://aws.amazon.com/blogs/machine-learning/build-multi-agent-site-reliability-engineering-assistants-with-amazon-bedrock-agentcore/ — **primary technical and competitive source**; fetched 2026-08-13.
2. Amazon Bedrock AgentCore Samples (GitHub, awslabs / AWS-linked samples referenced from the blog). https://github.com/awslabs/amazon-bedrock-agentcore-samples — supporting implementation reference; accessed 2026-08-13.
3. PagerDuty, “PagerDuty Report Reveals Some Organizations Lose More than $1 Million Per Hour During Unplanned Disruptions,” 17 Mar 2026. https://www.pagerduty.com/newsroom/2026-state-of-ai-first-operations/
4. PagerDuty, 2026 State of AI-First Operations (Wakefield Research, n=1,000). https://www.pagerduty.com/state-of-ai-first-operations/
5. PagerDuty, “How to Reduce MTTR - 2026 Guide.” https://www.pagerduty.com/resources/incident-management-response/learn/reduce-mttr-2026-guide/
6. Datadog, “Datadog Launches Bits AI SRE Agent to Resolve Incidents Faster,” 2 Dec 2025. https://www.datadoghq.com/about/latest-news/press-releases/datadog-launches-bits-ai-sre-agent-to-resolve-incidents-faster/
7. Datadog, “Introducing Bits Investigation, your AI on-call teammate.” https://www.datadoghq.com/blog/bits-ai-sre/
8. Microsoft, Azure SRE Agent product page. https://azure.microsoft.com/en-us/products/sre-agent
9. Microsoft Tech Community, “What's new in Azure SRE Agent in the GA release,” 10 Mar 2026. https://techcommunity.microsoft.com/blog/appsonazureblog/whats-new-in-azure-sre-agent-in-the-ga-release/4500779
10. Mordor Intelligence, AIOps Market (size, SRE practice 48% in 2025). https://www.mordorintelligence.com/industry-reports/aiops-market
11. Mordor Intelligence, Observability Market. https://www.mordorintelligence.com/industry-reports/observability-market
12. Expert Market Research, AIOps Market Size (USD 33.19B in 2025 cited). https://www.expertmarketresearch.com/reports/aiops-market
13. The Business Research Company, Algorithmic IT Operations (AIOps) global market report (2025–2030 figures). https://www.thebusinessresearchcompany.com/report/algorithmic-it-operations-aiops-global-market-report
14. Dataintelo, Service Reliability Engineering Platform Market (USD 6.8B in 2025). https://dataintelo.com/report/service-reliability-engineering-platform-market
15. JustAnalytics, APM and Observability Market Statistics 2026 (Gartner-linked ~$21B). https://justanalytics.app/blog/apm-market-statistics-and-trends-2026
16. Analysis Atlas, Observability and APM Market Analysis 2026 (Bits GA date; Resolve AI funding recap). https://analysis-atlas.com/research/observability-apm-market-analysis/
17. Zylos Research, “AIOps: AI-Driven IT Operations…” (2024–2029 AIOps size path). https://zylos.ai/research/2026-02-10-aiops/
18. incident.io, “3 best PagerDuty alternatives 2025” (pricing/positioning; vendor-authored). https://incident.io/blog/3-best-pagerduty-alternatives-2025-comparison
19. Rootly, incident platform comparisons (PagerDuty / Opsgenie / Rootly). https://rootly.com/sre/pagerduty-vs-rootly-vs-opsgenie-a-modern-comparison
20. StackFYI, Incident Management Tools Compared 2026. https://www.stackfyi.com/guides/incident-management-tools-compared-2026
21. SonarOps / Network Installers recaps of Splunk-Cisco Hidden Costs of Downtime 2026 and EMA/BigPanda 2024 per-minute costs (secondary). https://www.sonarops.it/blog/average-cost-of-downtime-by-industry-2026 ; https://thenetworkinstallers.com/blog/cost-of-it-downtime-statistics/
22. Gergely Orosz, “How AWS deals with a major outage,” The Pragmatic Engineer (Oct 2025 us-east-1 operational complexity). https://newsletter.pragmaticengineer.com/p/how-aws-deals-with-a-major-outage
23. Model Context Protocol documentation (linked from AWS blog). https://modelcontextprotocol.io
24. LangGraph documentation (framework used in AWS SRE sample). https://www.langchain.com/langgraph
25. AAMAD in-repo: `.cursor/templates/mrd-template.md`, `.cursor/rules/adapter-registry.mdc`, `.cursor/rules/adapter-crewai.mdc`, `aamad.config.example.yml`.

**Conflicting information.** AIOps/observability TAM figures disagree by 2–3× depending on category definition (platform vs services vs “AI observability” subset). PagerDuty hourly-loss percentages are survey self-reports, not measured ledger costs. AWS 30–45→5–10 minute investigation improvement and Datadog “90% faster” claims are vendor-reported. This MRD does not pick a single TAM; it uses incident-cost and investigation-time as the decision-relevant evidence.

---

## Assumptions

- The user request is commercial/market-facing, so MRD is required (not skipped).
- Product concept is a **multi-agent SRE incident assistant**, inferred from the problem statement that the AWS article also uses; no prior `system-description.md` existed.
- `AAMAD_TARGET_RUNTIME` is unset; resolved default is `crewai` per adapter registry.
- `aamad.config.yml` is absent; `aamad.config.example.yml` is not treated as binding, but its `security.require_security_assessment: true` is noted for later Deliver.
- AWS demo metrics (33× latency, synthetic pod names) are **UX fixtures**, not market statistics.
- AgentCore is a **candidate AWS runtime/integration**, not a fourth AAMAD adapter, until the registry is extended.
- MVP targets investigation assistance with stub infrastructure APIs, analogous to the AWS sample’s synthetic backends.
- Patent landscape was not searched; no FTO claim is made.

---

## Open Questions

1. Should elicitation lock telemetry vendors (Datadog vs Prometheus/Grafana vs CloudWatch) before PRD, or stay stub-neutral?
2. Will the operator extend AAMAD’s adapter registry to include Bedrock AgentCore, or keep AgentCore as deploy-only?
3. Is mutating remediation in-scope for v1 with HITL, or explicitly banned until after QA?
4. Primary channel: AAMAD chat UI only, or Slack-first like incident.io/Rootly?
5. Target customer: internal platform team vs external commercial product (pricing, SOC2)?
6. Which LLM budget and data-residency constraints apply (Bedrock vs direct Anthropic vs Azure)?
7. Does financial-services / DORA two-hour recovery apply to the first customer, adding audit-log requirements?
8. How should Alice/Carol memory personas map to MVP roles (single SRE persona vs multi-audience reports)?

---

## Audit

- **Timestamp:** 2026-08-13T20:45:00-04:00
- **Persona id:** `product-mgr`
- **Action:** `create-mrd`
- **Resolved runtime:** `crewai` (default; `AAMAD_TARGET_RUNTIME` unset). Amazon Bedrock AgentCore recorded as optional AWS hosting/MCP gateway path, not as `AAMAD_TARGET_RUNTIME`.
- **Prompt Trace:** Omitted from this artifact to avoid embedding long third-party article text and to keep traces free of any future secrets. Research inputs were the operator problem statement, `.cursor/templates/mrd-template.md`, and fetched public URLs listed in Sources (primary: AWS AgentCore SRE blog, 2026-08-13).
- **Tooling:** WebFetch of AWS ML Blog URL; WebSearch of PagerDuty, Datadog, Azure, AIOps/observability analyst pages; read of AAMAD MRD template and product-mgr contract. No application code was modified.
- **Model / determinism:** IDE agent session; market figures copied from cited pages rather than estimated. Temperature/max_tokens of upstream vendor models used inside AWS/Datadog products are not controlled here.
- **Template self-check:** Executive Summary; Detailed Findings (dimensions 1–5); Critical Decision Points; Risk Assessment Matrix; Actionable Recommendations; Sources; Assumptions; Open Questions; Audit — present.
- **Primary-source incorporation:** AWS AgentCore SRE article cited in Executive Summary, Dimension 1 (gaps + competitive landscape), Dimension 2 (architecture, MCP tools, runtimes), Dimension 3 (UX/HITL), Dimension 4 (Runtime/Identity/Observability), Dimension 5 (differentiation), Sources, Assumptions, and this Audit.
