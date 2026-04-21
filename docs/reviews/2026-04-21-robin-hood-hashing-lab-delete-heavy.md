# Robin Hood hashing lab review — 2026-04-21 — delete-heavy benchmark slice

## Research note
- Briefly rechecked the backward-shift deletion story against Emmanuel Goossaert's write-up on Robin Hood hashing deletion (`https://codecapsule.com/2013/11/17/robin-hood-hashing-backward-shift-deletion/`), which explicitly calls out that backward-shift deletion keeps mean/variance low after removals. That matched the goal of adding post-delete benchmark artifacts instead of only fill-only comparisons.

## Pass 1 — report semantics review
- Re-read the generated Markdown report as if a reviewer only saw the exported artifact, not the code.
- Issue found: the report said "Start load factor" even though capacities like `31` round the requested `0.25` target to `8` entries (`0.2581` effective load), which made fill-only rows look inconsistent.
- Fix: relabeled report/dashboard tables and histogram headers to "Requested load factor", and added an explicit rounding note to the README plus Markdown/HTML reports.

## Pass 2 — delete-path correctness review
- Re-audited the delete-heavy path from `run_benchmark(...)` through both table implementations instead of trusting the new metrics fields.
- Issue found: the linear-probing baseline must preserve wrapped keys after deletion or the delete-heavy comparison becomes misleading.
- Fix: locked that behavior down with `test_linear_probing_delete_keeps_later_wrapped_keys_searchable`, then re-ran the benchmark/export path to confirm the baseline stayed searchable after removals.

## Pass 3 — artifact contract review
- Reviewed the CLI/export surface as if a recruiter or student only consumed the committed sample artifacts.
- Issue found: adding workload-aware benchmarking changed the report/output contract in four places at once (CSV, JSON, Markdown, HTML), so stale headers/assertions would have left the sample bundle inconsistent.
- Fix: extended the benchmark rows, summary rendering, CLI export tests, README, and committed artifact bundle so `fill-only` and `delete-heavy` stay aligned everywhere.

## Pass 4 — determinism and hygiene review
- Re-ran the same benchmark twice into separate temp directories after the wording/export fixes.
- Result: Markdown, HTML, CSV, and JSON outputs stayed byte-for-byte deterministic across repeated runs, and `git diff --check` stayed clean.

## Final verification
- `python3 -m py_compile projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py tests/test_robin_hood_hashing_lab.py`
- `python3 -m unittest tests.test_robin_hood_hashing_lab -v` (`18/18`)
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --workloads fill-only,delete-heavy --delete-fraction 0.3 --markdown-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-report.md --html-out docs/artifacts/robin-hood-hashing-lab/sample-benchmark-dashboard.html --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.csv`
- `python3 projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py benchmark --capacity 31 --load-factors 0.25,0.5,0.75 --trials 3 --seed 17 --strategies robin-hood,linear-probing --workloads fill-only,delete-heavy --delete-fraction 0.3 --output docs/artifacts/robin-hood-hashing-lab/sample-benchmark.json`
- repeated the benchmark export into temp directories and verified `cmp` across Markdown/HTML/CSV/JSON outputs
- `git diff --check`
