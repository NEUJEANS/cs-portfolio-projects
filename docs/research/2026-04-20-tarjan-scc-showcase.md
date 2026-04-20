# Tarjan SCC showcase landing-page research — 2026-04-20

## Why external web research was skipped
- This slice does not introduce a new algorithm or browser/rendering dependency.
- The repo already contains proven static-showcase patterns (`regex-engine-lab`, `minhash-near-duplicate-lab`) that cover the exact design problem: combine existing artifacts into a recruiter-friendly landing page with relative links.
- Tarjan SCC already exposes the needed data locally via `explain`, `condensation`, and `compare`, so the gap is composition rather than outside knowledge.

## Repo-local references used instead
- `projects/regex-engine-lab/regex_engine_lab.py` — combined showcase page pattern for linking multiple artifact families from one HTML hub.
- `projects/minhash-near-duplicate-lab/minhash_lab.py` — landing-page pattern for stable relative links across committed artifact bundles.

## Decision
Build a lightweight `showcase-demo` command inside `tarjan_scc_lab.py` that reuses existing summary/benchmark data, validates any linked companion artifacts, and renders Markdown/HTML landing pages without adding a frontend build step.
