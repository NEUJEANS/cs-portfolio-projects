# Regex engine showcase explainer slice research — 2026-04-19

## Brief research
- No external web research was needed for this slice because the missing value was portfolio packaging around already-implemented repo-local `explain()` output.
- The strongest next step after the combined showcase page was to bridge the gap between raw trace JSON and broad benchmark dashboards with a tiny structure-first explanation layer.
- The existing explain payload already exposes an AST plus compiled Thompson-NFA states, so the slice should summarize that data rather than introducing a separate artifact format or duplicating parser/compiler logic.

## Slice decision
Add compact AST/NFA explainer cards to `showcase-demo` so each trace example gets:
- a one-line AST story
- AST shape/feature counts
- NFA shape metrics
- links back to the same benchmark dashboards already matched by pattern + mode

Why this is the right next slice:
- it completes the exact follow-up left in the README/checklist after the showcase page shipped
- it makes the portfolio easier for non-compiler specialists to skim before they open raw trace JSON
- it stays static, reproducible, and resumable because the showcase still regenerates from committed artifacts plus current engine explain output
