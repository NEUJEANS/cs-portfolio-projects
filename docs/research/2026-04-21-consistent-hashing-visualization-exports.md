# 2026-04-21 consistent-hashing visualization export research note

## Goal
Upgrade `consistent-hashing-lab` so it can generate portfolio-ready visuals of the ring itself instead of stopping at JSON and benchmark tables.

## Research summary
- A strong consistent-hashing portfolio artifact should show three things together: where virtual nodes land on the ring, which physical node owns a sample of keys, and how balanced the resulting load looks.
- Static SVG and self-contained HTML are a good fit for this repo because they stay deterministic, can be committed directly, and work well for README screenshots or slide exports.
- Visualizations need a readability cap for sample keys. The full load report can cover many keys, but the ring overlay should only draw a curated subset.

## Design chosen for this slice
- add a `visualize` command that reuses the existing deterministic ring and assignment logic
- render all virtual-node points around a circular SVG ring, then overlay a smaller sample of key markers inside the ring
- include load bars and an assignment table in both SVG and HTML so the artifact is understandable without opening raw JSON
- keep stdout as JSON, but summarize ring points instead of dumping the full internal list

## Notes
A web search was attempted for this slice, but the search provider returned a quota error, so the implementation falls back to standard visualization and portfolio-artifact practices already used elsewhere in the repo.
