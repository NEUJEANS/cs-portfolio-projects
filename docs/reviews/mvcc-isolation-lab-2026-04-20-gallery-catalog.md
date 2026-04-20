# MVCC isolation lab review — 2026-04-20 — gallery/catalog slice

## Pass 1 — committed artifact freshness
- Re-read the generated landing-page artifact against the in-progress `catalog` implementation instead of assuming the checked-out files were current.
- Issue found: the repo artifact bundle had not been regenerated yet, so the tracked `docs/artifacts/mvcc-isolation-lab/index.*` landing page was missing the first-dashboard hero shortcut that the current code already knew how to emit.
- Fix: reran the new `catalog` command into `docs/artifacts/mvcc-isolation-lab/` so the committed artifact bundle matches the implementation and is ready for GitHub browsing.

## Pass 2 — per-scenario anomaly visibility
- Re-read the HTML cards as if a recruiter landed directly on the gallery without opening the README or the scenario dashboards.
- Issue found: each card highlighted safe modes and abort counts, but the anomaly count for that scenario was hidden, which made the contrast between safer and weaker isolation levels less legible than it should be.
- Fix: added an `Anomaly modes` fact row to every scenario card and extended tests to lock the wording into the generated HTML.

## Pass 3 — future refresh discoverability
- Re-read the Markdown landing page as a resumable maintenance artifact instead of only a presentation artifact.
- Issue found: the generated page linked the artifacts well, but it did not tell future-me how to rebuild the full bundle after adding or editing scenarios.
- Fix: added a concise regenerate command hint near the top of the Markdown landing page and covered it in the render test.

## Final verification
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py catalog projects/mvcc-isolation-lab --output-dir docs/artifacts/mvcc-isolation-lab`
- deterministic double-export hash check for `docs/artifacts/mvcc-isolation-lab/index.html` and `docs/artifacts/mvcc-isolation-lab/index.md`
- `git diff --check`
