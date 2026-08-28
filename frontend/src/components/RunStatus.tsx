interface RunStatusProps {
  runId: string | null;
  planPreview?: string | null;
  stubData?: boolean;
}

export function RunStatus({ runId, planPreview, stubData }: RunStatusProps) {
  return (
    <section className="panel" aria-labelledby="run-heading" aria-live="polite">
      <h2 id="run-heading">Run</h2>
      <p className="status-pill">running</p>
      {stubData !== false ? (
        <p className="stub-banner" role="status">
          Demo / stub data — not live cluster telemetry.
        </p>
      ) : null}
      <p>Investigation in progress…</p>
      {runId ? (
        <p className="mono muted">
          runId: <span>{runId}</span>
        </p>
      ) : null}
      {planPreview ? (
        <pre className="plan-preview" aria-label="Investigation plan">
          {planPreview}
        </pre>
      ) : null}
    </section>
  );
}
