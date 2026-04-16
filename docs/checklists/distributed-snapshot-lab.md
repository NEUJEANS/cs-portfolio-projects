# Distributed Snapshot Lab Checklist

- [x] research a compact but interview-strong distributed snapshot project
- [x] refresh snapshot/marker/channel-state concepts and write a short self-test
- [x] implement a bank-transfer simulation with directed channels
- [x] implement Chandy-Lamport-style snapshot capture with delayed-marker modeling
- [x] add README usage examples and interview talking points
- [x] add unit and CLI tests for invariants and in-flight message capture
- [x] run at least 3 review passes and record fixes
- [x] add Mermaid visualization export for README/blog/interview demos
- [x] support multiple concurrent snapshots with named snapshot IDs and isolated results
- [x] add failure/recovery scripting with process liveness and scripted scenario playback
- [x] future slice: model explicit network partitions or link-level failures separately from process crashes
- [x] future slice: add scripted partition-heal walkthrough assets or richer per-link visualization notes
- [x] future slice: render walkthrough diagrams directly to SVG for project pages and slide decks
- [x] future slice: add PNG raster export for presentation tools that do not embed SVG cleanly
- [x] future slice: generate a single-page HTML or PDF handout that bundles the walkthrough narrative with committed SVG/PNG assets

## HTML handout slice (2026-04-16 20:47 UTC run)
- [x] confirm repo sync before editing
- [x] pick the remaining publishability gap from the distributed-snapshot checklist
- [x] skip external web research because the HTML handout is a direct extension of the existing walkthrough + asset pipeline
- [x] do a short HTML `picture` / relative-asset-link refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add optional `--html-output` support that renders a single-page handout from the same walkthrough result
- [x] keep Markdown walkthrough output intact while bundling timeline, summary cards, per-snapshot notes, Mermaid source, and committed SVG/PNG links in the handout
- [x] extend automated coverage for HTML rendering and CLI export behavior
- [x] regenerate the committed partition-heal handout artifact
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
