import type { HistoryEntry } from "../types";

interface ResultsViewProps {
  entry: HistoryEntry;
  onNewRun: () => void;
}

export function ResultsView({ entry, onNewRun }: ResultsViewProps) {
  return (
    <section className="panel" aria-labelledby="results-heading">
      <h2 id="results-heading">Results</h2>
      <p className="stub-banner" role="status">
        Demo / stub data — not live cluster telemetry.
      </p>
      <p className="mono muted">runId: {entry.runId}</p>
      <p className="muted">Completed: {entry.completedAt}</p>
      <h3>Summary</h3>
      <p>{entry.summary}</p>
      <h3>Findings</h3>
      <ul className="findings">
        {entry.findings.map((f) => (
          <li key={f.sourceId}>
            <strong>{f.specialist}</strong>: {f.text}{" "}
            <span className="mono muted">[{f.sourceId}]</span>
          </li>
        ))}
      </ul>
      <h3>Sources</h3>
      <p className="mono">{entry.sources.join(", ")}</p>
      <button type="button" onClick={onNewRun}>
        New research run
      </button>
    </section>
  );
}
