import type { HistoryEntry } from "../types";

interface HistoryPanelProps {
  entries: HistoryEntry[];
  selectedRunId: string | null;
  onSelect: (runId: string) => void;
}

export function HistoryPanel({
  entries,
  selectedRunId,
  onSelect,
}: HistoryPanelProps) {
  return (
    <section className="panel" aria-labelledby="history-heading">
      <h2 id="history-heading">History</h2>
      <p className="muted">
        Session-local only. Durable investigation history is Future Work
        (FR-105/FR-106).
      </p>
      {entries.length === 0 ? (
        <p className="muted">No completed runs in this session.</p>
      ) : (
        <ul className="history-list">
          {entries.map((entry) => (
            <li key={entry.runId}>
              <button
                type="button"
                className={
                  entry.runId === selectedRunId ? "history-item active" : "history-item"
                }
                onClick={() => onSelect(entry.runId)}
              >
                <span className="mono">{entry.runId.slice(0, 8)}…</span>
                <span>{entry.symptomPreview}</span>
                <span className="muted">{entry.completedAt}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
