interface RunStatusProps {
  runId: string | null;
}

export function RunStatus({ runId }: RunStatusProps) {
  return (
    <section className="panel" aria-labelledby="run-heading" aria-live="polite">
      <h2 id="run-heading">Run</h2>
      <p className="status-pill">running</p>
      <p>Investigation in progress…</p>
      {runId ? (
        <p className="mono muted">
          runId: <span>{runId}</span>
        </p>
      ) : null}
    </section>
  );
}
