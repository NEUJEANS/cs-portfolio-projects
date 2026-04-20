# Dependency graph planner review — 2026-04-20 — stochastic benchmark slice

## Pass 1 — docs / checklist review
- Re-read the planner README, project checklist, project slice checklist, and benchmark-suite manifest after the in-progress stochastic-benchmark code landed.
- Issue found: the repo story still documented only deterministic benchmark-suite scenarios, and the checklist trail did not yet show the uncertainty slice as completed work.
- Fix: updated `projects/dependency-graph-planner/README.md`, `projects/dependency-graph-planner/CHECKLIST.md`, `docs/checklists/dependency-graph-planner.md`, and added `docs/checklists/2026-04-20-dependency-graph-stochastic-benchmark-slice.md` so the new scenario field and completed slice are visible in-repo.

## Pass 2 — regression / validation review
- Re-read the stochastic benchmark payload path instead of assuming the new uncertainty metrics were already covered by the existing deterministic benchmark tests.
- Issue found: the new `stochastic_durations` path had no direct regression coverage for payload/report output, and invalid triangular-factor ordering was not pinned by a dedicated test.
- Fix: extended `projects/dependency-graph-planner/test_dependency_graph_planner.py` with coverage for stochastic benchmark payload/report metrics and invalid `low_factor <= mode_factor <= high_factor` validation.

## Pass 3 — artifact / reproducibility review
- Replayed the portfolio benchmark export workflow and deterministic double-run hash check with the stochastic duration configs that were supposed to be part of the committed showcase bundle.
- Issue found: the code supported stochastic suite scenarios locally, but the committed suite manifest and benchmark artifact bundle still reflected the older deterministic-only portfolio story.
- Fix: updated `projects/dependency-graph-planner/portfolio_benchmark_suite.json` to opt the seeded stress scenarios into stochastic replays, regenerated the Markdown/HTML/JSON/CSV benchmark artifact bundle, and verified repeat runs produced identical hashes.

## Final verification
- `python3 -m py_compile projects/dependency-graph-planner/dependency_graph_planner.py projects/dependency-graph-planner/test_dependency_graph_planner.py`
- `python3 -m unittest discover -s projects/dependency-graph-planner -p 'test_*.py' -v` (`55/55`)
- reran the benchmark suite with Markdown/HTML/JSON/CSV exports and confirmed the suite now reports `11` scenarios with `3` stochastic stress scenarios
- deterministic double-export hash check for the benchmark JSON payload
- `git diff --check`
