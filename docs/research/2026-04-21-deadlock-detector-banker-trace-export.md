# Deadlock detector Banker trace/export slice research

## Goal
Add a portfolio-friendly trace/export layer to the existing Banker's algorithm support so a reader can follow why a state is safe or why a request is denied.

## Brief notes
- The classic safety check is easiest to explain when each completed step shows the `work` vector before the choice, the runnable processes at that moment, the chosen process, and the allocation released back into `work`.
- Unsafe states should not just say `safe: false`; they should also report which unfinished processes are blocked and the exact per-resource shortages at the stall point.
- Request evaluation becomes much easier to demo when the hypothetical post-request state is preserved separately from the current state. That keeps denied requests explainable without pretending the unsafe grant actually happened.
- Markdown export is enough for this slice because it creates recruiter-friendly artifacts without pulling in heavier visualization dependencies yet.

## Sources
- GeeksforGeeks, "Program for Banker's Algorithm | Set 1 (Safety Algorithm)" for standard safety-check vocabulary and the `work` / `need` / safe-sequence framing.
- Existing deadlock-detector project docs and the prior 2026-04-15 Banker's slice wrap-up, which already identified trace/export support as the next missing demo-oriented improvement.
