import type { ReportLine } from "../types";

export type RunStatus = "running" | "done" | "error";

export interface StartRunPayload {
  symptom: string;
}

export interface StartRunResponse {
  runId: string;
  status: "running";
}

export interface RunFinding {
  specialist: string;
  text: string;
  sourceId: string;
}

export interface GetRunStatusResponse {
  runId: string;
  status: RunStatus;
  summary?: string;
  findings?: RunFinding[];
  sources?: string[];
  completedAt?: string;
  errorMessage?: string;
  planPreview?: string;
  stubData?: boolean;
  keyInsights?: ReportLine[];
  nextSteps?: ReportLine[];
  criticalAlerts?: ReportLine[];
  troubleshootingSteps?: ReportLine[];
}

interface ErrorEnvelope {
  error?: { code?: string; message?: string; diagnostic?: string };
}

export interface InvestigationSnapshot {
  investigation_id?: string;
  status?: string;
  plan?: unknown;
  specialist_results?: unknown[];
  report?: unknown;
  diagnostic?: unknown;
  stub_data?: boolean;
  error?: ErrorEnvelope["error"];
}

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw === "") {
    return "";
  }
  return (raw ?? "http://127.0.0.1:8000").replace(/\/$/, "");
}

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ErrorEnvelope;
    const code = body.error?.code;
    const message = body.error?.message;
    if (code && message) {
      return `${code}: ${message}`;
    }
    if (message) {
      return message;
    }
  } catch {
    /* fall through */
  }
  return `Request failed (${response.status})`;
}

/** Start investigation: POST /v1/investigations?wait=false → 202. */
export async function startRun(
  payload: StartRunPayload,
): Promise<StartRunResponse> {
  const symptom = payload.symptom.trim();
  if (!symptom) {
    throw new Error("symptom is required");
  }
  if (symptom.length > 8192) {
    throw new Error("symptom exceeds 8192 characters");
  }

  const response = await fetch(`${apiBase()}/v1/investigations?wait=false`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ symptom }),
  });

  if (!response.ok) {
    throw new Error(await readError(response));
  }

  const body = (await response.json()) as InvestigationSnapshot;
  const runId = body.investigation_id;
  if (!runId) {
    throw new Error("Backend did not return investigation_id.");
  }
  return { runId, status: "running" };
}

/** Poll investigation: GET /v1/investigations/{id}. */
export async function getRunStatus(runId: string): Promise<GetRunStatusResponse> {
  const response = await fetch(`${apiBase()}/v1/investigations/${runId}`, {
    headers: { Accept: "application/json" },
  });

  if (response.status === 404) {
    return { runId, status: "error", errorMessage: `Unknown runId: ${runId}` };
  }
  if (!response.ok) {
    return { runId, status: "error", errorMessage: await readError(response) };
  }

  const body = (await response.json()) as InvestigationSnapshot;
  return mapSnapshot(runId, body);
}

export function mapSnapshot(
  runId: string,
  body: InvestigationSnapshot,
): GetRunStatusResponse {
  const backendStatus = body.status ?? "running";
  if (backendStatus === "running") {
    return {
      runId,
      status: "running",
      planPreview: formatPlan(body.plan),
      stubData: body.stub_data === true,
    };
  }

  if (backendStatus === "failed") {
    return {
      runId,
      status: "error",
      errorMessage: failedMessage(body.diagnostic),
    };
  }

  const findings = collectFindings(body);
  const report = extractReport(body, findings);
  const sources = uniqueSources(report, findings);
  const summary = firstSummary(body, findings, report.keyInsights);
  return {
    runId: body.investigation_id ?? runId,
    status: "done",
    summary,
    findings,
    sources,
    completedAt: new Date().toISOString(),
    planPreview: formatPlan(body.plan),
    stubData: body.stub_data !== false,
    keyInsights: report.keyInsights,
    nextSteps: report.nextSteps,
    criticalAlerts: report.criticalAlerts,
    troubleshootingSteps: report.troubleshootingSteps,
  };
}

function extractReport(
  body: InvestigationSnapshot,
  findings: RunFinding[],
): {
  keyInsights: ReportLine[];
  nextSteps: ReportLine[];
  criticalAlerts: ReportLine[];
  troubleshootingSteps: ReportLine[];
} {
  const report = asRecord(body.report);
  const keyInsights = toReportLines(report.key_insights, "insight");
  const nextSteps = toReportLines(report.next_steps, "next_step");
  const criticalAlerts = toReportLines(report.critical_alerts, "alert");
  const troubleshootingSteps = toReportLines(
    report.troubleshooting_steps,
    "troubleshoot",
  );
  if (keyInsights.length === 0 && findings.length > 0) {
    return {
      keyInsights: findings.map((finding) => ({
        text: finding.text,
        specialist: finding.specialist,
        sourceId: finding.sourceId,
      })),
      nextSteps,
      criticalAlerts,
      troubleshootingSteps,
    };
  }
  return { keyInsights, nextSteps, criticalAlerts, troubleshootingSteps };
}

function toReportLines(raw: unknown, kind: string): ReportLine[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.map((item, index) => {
    if (typeof item === "string") {
      return { text: item };
    }
    const record = asRecord(item);
    const source = asRecord(record.source);
    const sourceId =
      source.record_id || source.tool
        ? `${kind}:${index}:${String(source.record_id ?? source.tool)}`
        : undefined;
    const executed =
      typeof record.executed === "boolean" ? record.executed : undefined;
    return {
      text: String(record.text ?? record.description ?? JSON.stringify(item)),
      specialist:
        typeof record.specialist === "string" ? record.specialist : undefined,
      sourceId,
      executed,
    };
  });
}

function uniqueSources(
  report: {
    keyInsights: ReportLine[];
    nextSteps: ReportLine[];
    criticalAlerts: ReportLine[];
    troubleshootingSteps: ReportLine[];
  },
  findings: RunFinding[],
): string[] {
  const ids = [
    ...report.keyInsights,
    ...report.nextSteps,
    ...report.criticalAlerts,
    ...report.troubleshootingSteps,
  ]
    .map((line) => line.sourceId)
    .concat(findings.map((finding) => finding.sourceId))
    .filter((id): id is string => Boolean(id));
  return [...new Set(ids)];
}

function collectFindings(body: InvestigationSnapshot): RunFinding[] {
  const findings: RunFinding[] = [];
  const specialists = Array.isArray(body.specialist_results)
    ? body.specialist_results
    : [];

  specialists.forEach((raw, specIndex) => {
    const spec = asRecord(raw);
    const specialist = String(spec.specialist ?? `specialist_${specIndex}`);
    const insights = Array.isArray(spec.insights) ? spec.insights : [];
    insights.forEach((insightRaw, insightIndex) => {
      const insight = asRecord(insightRaw);
      const source = asRecord(insight.source);
      const sourceId = `${specialist}:${insightIndex}:${String(
        source.record_id ?? source.tool ?? "insight",
      )}`;
      findings.push({
        specialist,
        text: String(insight.text ?? JSON.stringify(insightRaw)),
        sourceId,
      });
    });
    const emptyTools = Array.isArray(spec.empty_tools) ? spec.empty_tools : [];
    emptyTools.forEach((tool) => {
      findings.push({
        specialist,
        text: `no data from ${String(tool)}`,
        sourceId: `empty:${tool}`,
      });
    });
  });

  if (findings.length === 0) {
    const report = asRecord(body.report);
    const insights = Array.isArray(report.key_insights) ? report.key_insights : [];
    insights.forEach((insightRaw, index) => {
      const insight = asRecord(insightRaw);
      const source = asRecord(insight.source);
      findings.push({
        specialist: String(insight.specialist ?? "supervisor"),
        text: String(insight.text ?? JSON.stringify(insightRaw)),
        sourceId: `report:${index}:${String(source.record_id ?? source.tool ?? "insight")}`,
      });
    });
  }
  return findings;
}

function firstSummary(
  body: InvestigationSnapshot,
  findings: RunFinding[],
  keyInsights: ReportLine[],
): string {
  if (keyInsights.length > 0 && keyInsights[0].text) {
    return keyInsights[0].text;
  }
  const report = asRecord(body.report);
  const insights = Array.isArray(report.key_insights) ? report.key_insights : [];
  if (insights.length > 0) {
    const first = asRecord(insights[0]);
    if (first.text) {
      return String(first.text);
    }
  }
  if (findings.length > 0) {
    return findings[0].text;
  }
  return "Investigation completed.";
}

function formatPlan(plan: unknown): string | undefined {
  const record = asRecord(plan);
  const steps = Array.isArray(record.steps) ? record.steps : [];
  if (steps.length === 0) {
    return undefined;
  }
  return steps
    .map((stepRaw, index) => {
      const step = asRecord(stepRaw);
      const ordinal = step.ordinal ?? index + 1;
      const agent = step.agent ? ` (${step.agent})` : "";
      return `${ordinal}. ${String(step.description ?? "")}${agent}`;
    })
    .join("\n");
}

function failedMessage(diagnostic: unknown): string {
  if (typeof diagnostic === "string" && diagnostic.trim()) {
    return diagnostic;
  }
  const record = asRecord(diagnostic);
  const nested = asRecord(record.error);
  const message = nested.message ?? record.message;
  const code = nested.code ?? record.code;
  if (typeof code === "string" && typeof message === "string") {
    return `${code}: ${message}`;
  }
  if (typeof message === "string" && message.trim()) {
    return message;
  }
  if (typeof code === "string" && code.trim()) {
    return code;
  }
  return "Investigation failed.";
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}
