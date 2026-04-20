# Dependency graph planner review — 2026-04-20 — stress benchmark slice

## Pass 1 — docs / project-story review
- Re-read the planner README, project checklist, and benchmark-suite manifest after the in-progress stress-generator code landed.
- Issue found: the repo story still described only CI/release/data generators, and the checklist still listed the stress/lower-bound slice as unfinished.
- Fix: updated `projects/dependency-graph-planner/README.md`, `projects/dependency-graph-planner/CHECKLIST.md`, the dated slice checklist, and the long-form project checklist so the stress scenarios and lower-bound metrics are visible in-repo.

## Pass 2 — renderer / regression review
- Re-read the benchmark dashboard summary-card logic instead of assuming the aggregate leader also represented every secondary metric.
- Issue found: the "Lowest avg gap vs critical path" summary card incorrectly reused the top aggregate leader, which could silently report the wrong strategy whenever a different heuristic owned that metric.
- Fix: selected the lowest-gap strategy independently, surfaced the owning strategy in the summary card value, and added `test_render_benchmark_dashboard_html_summary_uses_lowest_gap_strategy`.

## Pass 3 — artifact / reproducibility review
- Replayed the generate+benchmark export workflow with the seeded stress manifests that were supposed to be part of the committed showcase bundle.
- Issue found: the repo had the in-progress suite/code changes locally, but the seeded stress manifests and refreshed benchmark Markdown/HTML/JSON/CSV artifacts were not yet committed, so the portfolio bundle still told the old story.
- Fix: generated `generated_stress_seed17.json`, `generated_stress_seed29.json`, and `generated_stress_seed41.json`, regenerated the benchmark artifact bundle, and verified deterministic double-export hashes.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v` (`53/53`)
- smoke-tested seeded stress manifest generation for seeds `17`, `29`, and `41`
- reran the benchmark suite with Markdown/HTML/JSON/CSV exports and confirmed the suite now covers `11` scenarios
- deterministic double-export hash check for the committed benchmark artifact bundle
- `git diff --check`
