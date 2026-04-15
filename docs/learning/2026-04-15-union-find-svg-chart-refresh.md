# Union-find SVG chart refresh — 2026-04-15

## Goal
Add a dependency-light charting slice to `union-find-network-lab` so committed benchmark and CSV-import artifacts can turn directly into portfolio-ready visuals.

## Quick refresh
- standalone SVG is a good fit for small CLIs because it is text-based, deterministic, and easy to diff in git
- a simple line chart only needs axes, projected points, labels, and a small amount of XML escaping
- for this project, benchmark-series artifacts already provide numeric `edges_requested` and `edges_per_second` pairs, while CSV-import snapshots provide `edge_index` and `stats.largest_component`
- keeping chart generation in pure Python avoids adding matplotlib or browser rendering dependencies to a beginner-friendly portfolio repo

## Self-test before coding
- define one helper that can normalize checked-in `.json` and `.csv` artifacts into a simple payload shape
- confirm the two chart families:
  - benchmark-series → x=`edges_requested`, y=`edges_per_second`
  - csv-import snapshots → x=`edge_index`, y=`stats.largest_component`
- keep output deterministic by using fixed SVG dimensions, fixed margins, and direct numeric labels from the artifact values
- guardrails to implement:
  - reject missing or non-numeric chart fields
  - require `snapshots` for csv-import chart rendering
  - reject unsupported artifact types early with clear CLI errors

## Done
The slice can be considered successful once the repo can export committed SVG charts during the main run and re-render them later from existing JSON/CSV artifacts via CLI.
