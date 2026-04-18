# crdt-orset-lab learning/self-test — 2026-04-18 — OR-Set vs LWW comparison slice

## Refresh
Only a short Python/CLI refresh was needed here: keep the comparison deterministic with explicit `time` fields in the JSON script, and treat the OR-Set timeline outputs as companion artifacts rather than trying to invent a second separate renderer for every model.

## Self-test checklist
- confirmed the half-finished local comparison code compiled cleanly after wiring the missing CLI path
- confirmed `compare-script` prints the full comparison JSON while still emitting OR-Set timeline artifacts through the existing export flags
- confirmed `sample_compare_ops.json` actually diverges at the end (`OR-Set -> notebook present`, `LWW -> notebook absent`)
- confirmed the generated HTML comparison page links the scenario script, OR-Set timeline bundle, and comparison Markdown/JSON outputs together

## Takeaway
For portfolio-oriented distributed-systems demos, the strongest artifact is usually not “more code” but a deterministic scenario that makes the trade-off obvious. Explicit timestamps turned this from a generic CRDT page into a concrete semantics comparison a student can actually explain in an interview.
