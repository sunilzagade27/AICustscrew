export type RunFsmState = "idle" | "running" | "done";

export type RunFsmEvent =
  | { type: "SUBMIT_VALID" }
  | { type: "STATUS_DONE" }
  | { type: "STATUS_ERROR" }
  | { type: "RESET" }
  | { type: "NEW_RUN" };

/** Lightweight FSM: idle → running → done */
export function transitionRunFsm(
  state: RunFsmState,
  event: RunFsmEvent,
): RunFsmState {
  switch (state) {
    case "idle":
      if (event.type === "SUBMIT_VALID") return "running";
      return state;
    case "running":
      if (event.type === "STATUS_DONE") return "done";
      if (event.type === "STATUS_ERROR" || event.type === "RESET") return "idle";
      return state;
    case "done":
      if (event.type === "RESET" || event.type === "NEW_RUN") return "idle";
      return state;
    default: {
      const _exhaustive: never = state;
      return _exhaustive;
    }
  }
}
