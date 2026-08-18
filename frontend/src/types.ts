export interface HistoryEntry {
  runId: string;
  symptomPreview: string;
  completedAt: string;
  status: "done";
  summary: string;
  findings: { specialist: string; text: string; sourceId: string }[];
  sources: string[];
}
