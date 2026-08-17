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
}

const STUB_DELAY_MS = 1200;
const store = new Map<
  string,
  {
    symptom: string;
    startedAt: number;
  }
>();

function newRunId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `run-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/** Stub: starts a research run; no live backend. */
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

  await delay(200);
  const runId = newRunId();
  store.set(runId, { symptom, startedAt: Date.now() });
  return { runId, status: "running" };
}

/** Stub: polls run status; completes after a short delay with canned results. */
export async function getRunStatus(runId: string): Promise<GetRunStatusResponse> {
  await delay(150);
  const entry = store.get(runId);
  if (!entry) {
    return {
      runId,
      status: "error",
      errorMessage: `Unknown runId: ${runId}`,
    };
  }

  const elapsed = Date.now() - entry.startedAt;
  if (elapsed < STUB_DELAY_MS) {
    return { runId, status: "running" };
  }

  const completedAt = new Date().toISOString();
  const findings: RunFinding[] = [
    {
      specialist: "kubernetes_specialist",
      text: `Stub: no CrashLoopBackOff pods matching symptom context (“${truncate(entry.symptom, 80)}”).`,
      sourceId: "stub-k8s-1",
    },
    {
      specialist: "logs_specialist",
      text: "Stub: error rate elevated in demo log window; correlate with deploy timestamp.",
      sourceId: "stub-logs-1",
    },
    {
      specialist: "metrics_specialist",
      text: "Stub: p99 latency +3x vs baseline in the last hour (demo series).",
      sourceId: "stub-metrics-1",
    },
    {
      specialist: "runbooks_specialist",
      text: "Stub: next step — verify recent rollout and check HPA saturation (read-only).",
      sourceId: "stub-runbook-1",
    },
  ];

  return {
    runId,
    status: "done",
    summary:
      "Stub cited hypothesis: latency/errors align with a recent deploy; confirm with read-only cluster checks before any change.",
    findings,
    sources: findings.map((f) => f.sourceId),
    completedAt,
  };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function truncate(value: string, max: number): string {
  return value.length <= max ? value : `${value.slice(0, max - 1)}…`;
}
