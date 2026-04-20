# Tarjan SCC showcase self-test — 2026-04-20

- Goal: add one polished landing page without duplicating the existing explain/condensation/benchmark renderers.
- Refresher: the page should summarize the graph itself, then link out to the deeper artifacts rather than rebuilding every view inside the showcase.
- Refresher: relative links must be computed from the landing-page output path so committed docs remain portable if the artifact directory is nested.
- Self-check notes:
  - keep `render_explain_text()` reusable so CLI `explain` output and showcase preview never drift
  - make `showcase-demo` require at least one output path (`--markdown-output` and/or `--html-output`)
  - validate optional linked artifact paths up front so committed landing pages do not silently ship broken links
  - keep the artifact sections optional so the showcase can still render a good standalone page even if only a subset of companion files is supplied
