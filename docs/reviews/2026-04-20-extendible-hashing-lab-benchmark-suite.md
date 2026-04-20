# Extendible hashing lab review — 2026-04-20 — benchmark-suite slice

## Pass 1 — portfolio-story / README review
- Re-read the project README and checklist from the perspective of someone landing on the repo after the delete/merge slice.
- Issue found: the unfinished local benchmark code existed, but the README still stopped at workload/delete flows and did not expose a benchmark command or committed benchmark artifacts.
- Fix: updated `projects/extendible-hashing-lab/README.md` plus the project/root checklists to document the new benchmark workflow and artifact bundle.

## Pass 2 — summary-robustness review
- Re-read the benchmark summarization code instead of trusting the happy-path output.
- Issue found: the summary reused the first trial's extendible metrics, final entry count, and operation mix without checking that later trials matched, so a future regression could be silently flattened into a misleading report.
- Fix: tightened `summarize_benchmark_trials(...)` to reject inconsistent operation counts, final entry counts, or extendible metrics across trials, and added `test_summarize_benchmark_trials_rejects_inconsistent_extendible_metrics`.

## Pass 3 — benchmark-story review
- Replayed the generated Markdown report as a recruiter-facing artifact rather than just a test fixture.
- Issue found: the scoreboard showed splits/merges but hid directory growth/shrink counts, which weakened the extendible-hashing-specific story versus cuckoo rehashes/displacements.
- Fix: expanded the Markdown scoreboard and scenario bullets to include directory grow/shrink counts, then regenerated the benchmark artifact bundle.

## Pass 4 — reproducibility review
- Re-ran the full benchmark export twice and compared the JSON/Markdown/CSV outputs byte-for-byte.
- Result: outputs matched exactly, so the committed artifact bundle is deterministic and safe to keep under version control.

## Final verification
- `python3 -m py_compile projects/extendible-hashing-lab/extendible_hashing_lab.py tests/test_extendible_hashing_lab.py`
- `python3 -m unittest tests.test_extendible_hashing_lab -v` (`19/19`)
- `python3 projects/extendible-hashing-lab/extendible_hashing_lab.py benchmark --input projects/extendible-hashing-lab/benchmark_suite.json --json-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.json --markdown-out docs/artifacts/extendible-hashing-lab/benchmark_suite_report.md --csv-out docs/artifacts/extendible-hashing-lab/benchmark_suite_summary.csv --title 'Extendible hashing vs cuckoo hashing benchmark comparison'`
- repeated the benchmark export into two temp directories and verified `cmp` across JSON/Markdown/CSV outputs
- `git diff --check`
