import { strict as assert } from "node:assert";
import { test } from "node:test";
import { transitionRunFsm, type RunFsmEvent, type RunFsmState } from "./runFsm.ts";

const events: RunFsmEvent["type"][] = [
  "SUBMIT_VALID",
  "STATUS_DONE",
  "STATUS_ERROR",
  "RESET",
  "NEW_RUN",
];

test("idle to running on valid submit (AC-001)", () => {
  assert.equal(transitionRunFsm("idle", { type: "SUBMIT_VALID" }), "running");
});

test("running to done on status done", () => {
  assert.equal(transitionRunFsm("running", { type: "STATUS_DONE" }), "done");
});

test("running to idle on error or reset (AC-002 failure path)", () => {
  assert.equal(transitionRunFsm("running", { type: "STATUS_ERROR" }), "idle");
  assert.equal(transitionRunFsm("running", { type: "RESET" }), "idle");
});

test("done to idle on new run", () => {
  assert.equal(transitionRunFsm("done", { type: "NEW_RUN" }), "idle");
  assert.equal(transitionRunFsm("done", { type: "RESET" }), "idle");
});

test("illegal transitions are no-ops", () => {
  const table: Array<[RunFsmState, RunFsmEvent["type"], RunFsmState]> = [
    ["idle", "STATUS_DONE", "idle"],
    ["idle", "STATUS_ERROR", "idle"],
    ["idle", "RESET", "idle"],
    ["idle", "NEW_RUN", "idle"],
    ["running", "SUBMIT_VALID", "running"],
    ["running", "NEW_RUN", "running"],
    ["done", "SUBMIT_VALID", "done"],
    ["done", "STATUS_DONE", "done"],
    ["done", "STATUS_ERROR", "done"],
  ];
  for (const [from, type, expected] of table) {
    assert.equal(transitionRunFsm(from, { type } as RunFsmEvent), expected);
  }
  assert.equal(events.length, 5);
});
