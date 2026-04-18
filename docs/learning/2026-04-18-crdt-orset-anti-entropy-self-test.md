# crdt-orset-lab learning/self-test — 2026-04-18 — anti-entropy slice

## Refresh
A compact refresh was enough here: the teaching value is not implementing a production replication protocol, but showing that an OR-Set sync can be discussed in terms of **full-state bytes**, **delta bytes**, and **what tags/tombstones/counters actually had to move**.

## Self-test checklist
- confirmed the anti-entropy helpers derive their numbers from canonical JSON payloads so digest/byte counts stay deterministic
- confirmed sync timeline events keep the pre-merge source/target views, which is the only moment when a meaningful transfer estimate exists
- confirmed the new report can be exported without inventing a second simulation path; it reuses the snapshot already produced by `run-script` / `compare-script`
- confirmed the output shape is suitable for both machine-readable JSON and browser-friendly HTML/Markdown artifacts

## Takeaway
For a portfolio project, an anti-entropy report is stronger than just saying “replicas merged.” It turns convergence into an explainable systems trade-off: when do you need the whole state, and when is the missing delta enough?
