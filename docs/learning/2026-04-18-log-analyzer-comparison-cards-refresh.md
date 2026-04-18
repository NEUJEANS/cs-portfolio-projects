# Learning refresh — 2026-04-18 — log-analyzer comparison-card slice

## Python/tool refresh
- Reuse the shipped `facet_comparison` result instead of inventing a second comparison pipeline.
- Keep SVG rendering pure/string-based like the existing time-bucket card helpers so the project stays standard-library only.
- HTML companion output should embed the SVG inline and add exact tables for verification/copy-paste.
- New export flags should validate exactly like the existing comparison CSV flag: they only make sense when `--facet-compare-field` and `--facet-compare-values` are active.
- A committed sample artifact bundle is worth adding here because this slice is specifically about screenshot-ready outputs.

## Self-test plan
- fix the current unfinished syntax break in the dirty comparison-card work first
- confirm helper output contains the compared facet labels, delta copy, and aligned bucket coverage details
- confirm CLI validation rejects comparison-card export flags without the required comparison arguments
- confirm real CLI runs write both SVG and HTML artifacts successfully
- confirm README/checklists mention the new flags and example artifact workflow
- confirm the existing comparison/time-bucket behavior stays green under the full test suite
