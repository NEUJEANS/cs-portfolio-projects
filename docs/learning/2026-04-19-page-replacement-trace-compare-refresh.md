# Learning refresh — 2026-04-19 — page replacement imported trace comparison

## Quick refresher
- this slice is still CLI/reporting work, not a new replacement policy, so extra web research was not needed before implementation
- the cleanest UX is a dedicated `trace-compare` subcommand that accepts `--pages-file` exactly twice instead of overloading the single-workload `compare` flow
- imported traces should stay visibly distinct in every artifact, so the payload, CSV rows, SVG legend text, and HTML tables all need stable left/right workload labels derived from file stems
- comparing traces with different lengths is more honest when the headline chart uses average page-fault rate per reference, while the detailed table still keeps raw average fault counts and per-frame fault totals
- portfolio artifacts are stronger when the same run emits Markdown, SVG, CSV, JSON, and HTML so screenshots, prose, and machine-readable outputs all stay consistent

## Self-check
A good `trace-compare` run should now:
- fail fast unless exactly two `--pages-file` inputs are provided
- emit `left` and `right` trace sections with `pages-file:` source labels in the JSON payload
- write one side-by-side Markdown / SVG / CSV / JSON / HTML bundle into the chosen artifact directory
- report which trace has the lower overall average fault rate while still showing per-algorithm and per-frame details
- keep the imported reference strings and locality summaries readable enough for an interview walkthrough

## Why this slice matters
- it turns imported traces into a portfolio storytelling tool instead of just one-off study inputs
- it gives students a compact way to contrast two realistic workloads, such as a locality-friendly mobile session versus a scan-heavy reporting session, without needing a notebook or custom plotting code
- it keeps the page-replacement lab extensible for later work like working-set policies or richer narrative write-ups around trace differences
