# Regex engine combined showcase refresh and self-test — 2026-04-19

## Refresh
- keep the showcase generator artifact-driven: it should read the committed trace/benchmark files and derive summaries instead of duplicating regex or benchmark logic
- prefer relative links from the output HTML page to the artifact directory so the showcase still works if the output file is moved within the repo tree
- use the benchmark report `case_definitions` metadata to connect trace cards to the dashboards that exercise the same regex pattern and mode
- keep the output as one static HTML page with no JS dependency so GitHub rendering and local file browsing stay simple

## Self-test
1. Why build the showcase from existing artifacts instead of adding another raw export format?
   - because the value is navigation and narrative glue, not new engine data; the existing trace and benchmark artifacts already contain the evidence.
2. What makes the trace-to-dashboard cross-links better than just listing files in one directory?
   - they preserve context: a reviewer can see which dashboards reuse the same regex case and jump from low-level state transitions to high-level benchmark results immediately.
3. Why insist on relative links and a static page?
   - that keeps the artifact portable, Git-friendly, and easy to regenerate without a dev server or frontend toolchain.
