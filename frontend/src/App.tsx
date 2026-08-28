import { useCallback, useEffect, useRef, useState } from "react";
import { InputsForm } from "./components/InputsForm";
import { RunStatus } from "./components/RunStatus";
import { ResultsView } from "./components/ResultsView";
import { HistoryPanel } from "./components/HistoryPanel";
import { transitionRunFsm, type RunFsmState } from "./fsm/runFsm";
import { getRunStatus, startRun } from "./services/runService";
import type { HistoryEntry } from "./types";
import "./App.css";

const POLL_MS = 1500;
const POLL_TIMEOUT_MS = 610_000;
const MAX_SYMPTOM = 8192;

export default function App() {
  const [fsm, setFsm] = useState<RunFsmState>("idle");
  const [symptom, setSymptom] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [planPreview, setPlanPreview] = useState<string | null>(null);
  const [activeResult, setActiveResult] = useState<HistoryEntry | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const pollRef = useRef<number | null>(null);

  const dispatch = useCallback((event: Parameters<typeof transitionRunFsm>[1]) => {
    setFsm((prev) => {
      const next = transitionRunFsm(prev, event);
      if (next === prev && import.meta.env.DEV) {
        console.debug("[runFsm] no-op", { prev, event });
      }
      return next;
    });
  }, []);

  const clearPoll = useCallback(() => {
    if (pollRef.current != null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => clearPoll(), [clearPoll]);

  async function handleSubmit() {
    const trimmed = symptom.trim();
    if (!trimmed) {
      setInputError("Enter a non-empty symptom or alert paste.");
      return;
    }
    if (trimmed.length > MAX_SYMPTOM) {
      setInputError(`Symptom must be at most ${MAX_SYMPTOM} characters.`);
      return;
    }

    setInputError(null);
    dispatch({ type: "SUBMIT_VALID" });

    try {
      const started = await startRun({ symptom: trimmed });
      setRunId(started.runId);
      setPlanPreview(null);
      setActiveResult(null);

      const startedAt = Date.now();
      const pollOnce = async () => {
        try {
          if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
            clearPoll();
            setInputError("Investigation timed out waiting for the backend (600s cap).");
            dispatch({ type: "STATUS_ERROR" });
            return;
          }
          const status = await getRunStatus(started.runId);
          if (status.planPreview) {
            setPlanPreview(status.planPreview);
          }
          if (status.status === "running") return;

          clearPoll();
          if (status.status === "error") {
            setInputError(status.errorMessage ?? "Run failed.");
            dispatch({ type: "STATUS_ERROR" });
            return;
          }

          const entry: HistoryEntry = {
            runId: status.runId,
            symptomPreview: trimmed.slice(0, 120),
            completedAt: status.completedAt ?? new Date().toISOString(),
            status: "done",
            summary: status.summary ?? "",
            findings: status.findings ?? [],
            sources: status.sources ?? [],
            stubData: status.stubData !== false,
            keyInsights: status.keyInsights ?? [],
            nextSteps: status.nextSteps ?? [],
            criticalAlerts: status.criticalAlerts ?? [],
            troubleshootingSteps: status.troubleshootingSteps ?? [],
          };
          setActiveResult(entry);
          setHistory((prev) => [entry, ...prev]);
          dispatch({ type: "STATUS_DONE" });
        } catch (err) {
          clearPoll();
          setInputError(err instanceof Error ? err.message : "Status poll failed.");
          dispatch({ type: "STATUS_ERROR" });
        }
      };

      clearPoll();
      void pollOnce();
      pollRef.current = window.setInterval(() => {
        void pollOnce();
      }, POLL_MS);
    } catch (err) {
      setInputError(err instanceof Error ? err.message : "Failed to start run.");
      dispatch({ type: "STATUS_ERROR" });
    }
  }

  function handleNewRun() {
    clearPoll();
    setRunId(null);
    setPlanPreview(null);
    setActiveResult(null);
    setInputError(null);
    dispatch({ type: "NEW_RUN" });
  }

  function handleSelectHistory(id: string) {
    const entry = history.find((h) => h.runId === id);
    if (!entry) return;
    clearPoll();
    setActiveResult(entry);
    setRunId(entry.runId);
    setFsm("done");
  }

  return (
    <div className="app">
      <header className="header">
        <p className="brand">AICustscrew</p>
        <h1>Critical Research Workflow</h1>
        <p className="muted">
          Single route · FSM: <span className="mono">{fsm}</span>
        </p>
        <p className="muted future-work">
          Future Work: Slack/Teams intake, PagerDuty inbound, executive report
          style, auto-remediation.
        </p>
      </header>

      <main className="layout">
        <div className="primary">
          {fsm === "idle" ? (
            <InputsForm
              symptom={symptom}
              error={inputError}
              disabled={false}
              onSymptomChange={setSymptom}
              onSubmit={handleSubmit}
            />
          ) : null}

          {fsm === "running" ? (
            <RunStatus runId={runId} planPreview={planPreview} stubData />
          ) : null}

          {fsm === "done" && activeResult ? (
            <ResultsView entry={activeResult} onNewRun={handleNewRun} />
          ) : null}
        </div>

        <aside>
          <HistoryPanel
            entries={history}
            selectedRunId={activeResult?.runId ?? null}
            onSelect={handleSelectHistory}
          />
        </aside>
      </main>
    </div>
  );
}
