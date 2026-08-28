import type { HistoryEntry, ReportLine } from "../types";

interface ResultsViewProps {
  entry: HistoryEntry;
  onNewRun: () => void;
}

export function ResultsView({ entry, onNewRun }: ResultsViewProps) {
  return (
    <section className="panel" aria-labelledby="results-heading">
      <h2 id="results-heading">Results</h2>
      {entry.stubData !== false ? (
        <p className="stub-banner" role="status">
          Demo / stub data — not live cluster telemetry.
        </p>
      ) : null}
      <p className="mono muted">runId: {entry.runId}</p>
      <p className="muted">Completed: {entry.completedAt}</p>
      <ReportSection title="Key Insights" lines={entry.keyInsights} />
      <ReportSection title="Next Steps" lines={entry.nextSteps} showExecuted />
      <ReportSection title="Critical Alerts" lines={entry.criticalAlerts} />
      <ReportSection
        title="Troubleshooting Steps"
        lines={entry.troubleshootingSteps}
      />
      <h3>Sources</h3>
      {entry.sources.length > 0 ? (
        <p className="mono">{entry.sources.join(", ")}</p>
      ) : (
        <p className="muted">No findings.</p>
      )}
      <button type="button" onClick={onNewRun}>
        New research run
      </button>
    </section>
  );
}

function ReportSection({
  title,
  lines,
  showExecuted = false,
}: {
  title: string;
  lines: ReportLine[];
  showExecuted?: boolean;
}) {
  return (
    <>
      <h3>{title}</h3>
      {lines.length === 0 ? (
        <p className="muted">No findings.</p>
      ) : (
        <ul className="findings">
          {lines.map((line, index) => (
            <li key={`${title}-${line.sourceId ?? index}`}>
              {line.specialist ? <strong>{line.specialist}: </strong> : null}
              {line.text}
              {showExecuted && line.executed === false ? (
                <span className="muted"> (not executed)</span>
              ) : null}
              {line.sourceId ? (
                <span className="mono muted"> [{line.sourceId}]</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
