# CRDT OR-Set Visualization Research Note — 2026-04-18

## Goal
Make `crdt-orset-lab` more portfolio-friendly by exporting the scripted replica story as committed visualization artifacts instead of only raw JSON.

## Brief research summary
- OR-Set explanations land better when the timeline shows **which tags existed at each step** and **which tags a remove actually observed**.
- Mermaid sequence diagrams are a lightweight way to show replica-local events and anti-entropy sync arrows without pulling in extra dependencies.
- A second static SVG artifact is still useful because it renders directly in GitHub/README contexts and is easy to screenshot for slides.

## Source notes
- Refreshed Mermaid sequence-diagram syntax from the official docs (`participant`, self-messages, cross-replica messages, and `Note over ...` usage).
- Reused the existing OR-Set semantics note from the earlier slice: removes only tombstone the add-tags a replica has observed, so concurrent/later adds can survive merge.

## Scope chosen for this slice
- keep the existing simulator/JSON output unchanged
- add optional timeline exports to the CLI instead of introducing a separate renderer tool
- generate Markdown, Mermaid, and SVG timeline artifacts from the same snapshot/timeline data
- commit a sample artifact bundle for `sample_ops.json`

## Deferred
- richer lattice/state-join diagrams
- animated browser playback
- side-by-side comparison with LWW-element-set timelines
