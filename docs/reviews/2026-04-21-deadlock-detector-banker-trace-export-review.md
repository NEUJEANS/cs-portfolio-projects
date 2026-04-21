# Deadlock detector Banker trace/export review log

## Pass 1, safety-sequence compatibility audit
- Checked that the new trace instrumentation did not silently change the established Banker's safe-sequence ordering.
- Found a regression: the first trace implementation picked the first runnable process from a freshly recomputed list, which changed the historic sample sequence from `P1, P3, P4, P0, P2` to `P1, P3, P0, P2, P4`.
- Fix: keep trace capture inside the original while/for scan order so the project stays deterministic and backward compatible while still recording runnable sets and `work` transitions.

## Pass 2, denied-request trace audit
- Checked the unsafe-request path to make sure exports explain the hypothetical post-request stall without pretending the denied grant actually became the live state.
- Fix: preserve the current state in `available` / `allocation` / `need`, add separate `trial_available` / `trial_allocation` / `trial_need` fields, and report blocking shortages from the simulated trial state.

## Pass 3, docs and artifact audit
- Checked README examples, sample artifacts, and test coverage for the new trace workflow.
- Fixes: documented `--markdown-out` for both Banker's commands, committed sample Markdown/JSON trace artifacts, and added CLI tests that verify trace JSON plus Markdown export behavior.
