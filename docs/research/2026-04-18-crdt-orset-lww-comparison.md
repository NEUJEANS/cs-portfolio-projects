# crdt-orset-lab research — 2026-04-18 — OR-Set vs LWW comparison slice

## Goal
Add a side-by-side explanation page that shows why an observed-remove set can keep an element that a last-write-wins element set drops.

## Scope decision
No heavy external research pass was needed for this slice because the work stayed within standard, already-established semantics:
- OR-Set removes only tags the replica has observed.
- LWW-element-set resolves conflicts by comparing add/remove timestamps, then applying the configured tie bias.

## What mattered for implementation
- the comparison scenario needed **explicit logical timestamps** so the divergence was deterministic instead of depending on operation order fallback
- the artifact bundle needed both the polished comparison page and the raw machine-readable JSON so the explanation stayed reproducible
- the README needed to explain that the comparison scenario is intentionally timestamped to make the semantic contrast visible

## Resulting implementation direction
1. ship a first-class `compare-script` CLI command
2. add a committed `sample_compare_ops.json` scenario whose final OR-Set membership is present while LWW is absent
3. generate Markdown / HTML / JSON comparison artifacts plus the linked OR-Set timeline bundle
