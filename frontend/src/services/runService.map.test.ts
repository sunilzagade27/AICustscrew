import { strict as assert } from "node:assert";
import { test } from "node:test";
import { mapSnapshot } from "./runService.ts";

const completeBody = {
  investigation_id: "inv-1",
  status: "complete",
  stub_data: true,
  plan: {
    steps: [
      {
        ordinal: 1,
        description: "Inspect payments-api pods",
        agent: "kubernetes_specialist",
      },
    ],
  },
  specialist_results: [
    {
      specialist: "kubernetes_specialist",
      insights: [
        {
          text: "pod CrashLoopBackOff",
          source: { tool: "get_pod_status", record_id: "pod/payments-api-7f9c-abc" },
        },
      ],
      empty_tools: ["get_node_status"],
    },
    { specialist: "logs_specialist", insights: [] },
    { specialist: "metrics_specialist", insights: [] },
    { specialist: "runbooks_specialist", insights: [] },
  ],
  report: {
    key_insights: [
      {
        text: "CrashLoopBackOff from missing ConfigMap",
        specialist: "kubernetes_specialist",
        source: { tool: "get_pod_status", record_id: "pod/payments-api-7f9c-abc" },
      },
    ],
    next_steps: [{ text: "Verify ConfigMap exists", executed: false }],
    critical_alerts: [],
    troubleshooting_steps: [{ text: "Read playbook rb-crashloop-configmap" }],
  },
};

test("running snapshot maps plan preview before report (AC-003)", () => {
  const mapped = mapSnapshot("inv-1", {
    status: "running",
    stub_data: true,
    plan: completeBody.plan,
  });
  assert.equal(mapped.status, "running");
  assert.match(mapped.planPreview ?? "", /kubernetes_specialist/);
  assert.equal(mapped.stubData, true);
  assert.equal(mapped.keyInsights, undefined);
});

test("complete snapshot maps AC-006 headings and citations (AC-005)", () => {
  const mapped = mapSnapshot("inv-1", completeBody);
  assert.equal(mapped.status, "done");
  assert.equal(mapped.runId, "inv-1");
  assert.ok((mapped.keyInsights ?? []).length >= 1);
  assert.equal(mapped.nextSteps?.[0]?.executed, false);
  assert.equal((mapped.criticalAlerts ?? []).length, 0);
  assert.ok((mapped.troubleshootingSteps ?? []).length >= 1);
  assert.ok((mapped.sources ?? []).some((id) => id.includes("pod/payments-api-7f9c-abc")));
});

test("empty_tools become honest no-data findings (AC-011)", () => {
  const mapped = mapSnapshot("inv-1", completeBody);
  const empty = (mapped.findings ?? []).find((row) => row.sourceId === "empty:get_node_status");
  assert.ok(empty);
  assert.match(empty.text, /no data from get_node_status/);
});

test("failed nested diagnostic maps to error (runtime failure path)", () => {
  const mapped = mapSnapshot("inv-1", {
    status: "failed",
    diagnostic: { error: { code: "LLM_UNAVAILABLE", message: "provider down" } },
  });
  assert.equal(mapped.status, "error");
  assert.equal(mapped.errorMessage, "LLM_UNAVAILABLE: provider down");
});
