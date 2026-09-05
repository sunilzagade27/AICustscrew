export interface ReportLine {
  text: string;
  sourceId?: string;
  specialist?: string;
  executed?: boolean;
}

export interface HistoryEntry {
  runId: string;
  symptomPreview: string;
  completedAt: string;
  status: "done";
  summary: string;
  findings: { specialist: string; text: string; sourceId: string }[];
  sources: string[];
  stubData: boolean;
  keyInsights: ReportLine[];
  nextSteps: ReportLine[];
  criticalAlerts: ReportLine[];
  troubleshootingSteps: ReportLine[];
}
