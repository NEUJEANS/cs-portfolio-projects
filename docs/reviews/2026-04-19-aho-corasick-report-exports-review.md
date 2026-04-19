# 2026-04-19 Aho-Corasick Report Export Review Log

## Review pass 1 — artifact usefulness
- Issue found: the first sample export command used `warning` / `critical`, which do not appear in the checked-in sample fixture, so the generated portfolio report was empty.
- Fix applied: switched the committed artifact workflow to `--pattern-file projects/aho-corasick-search-lab/sample_patterns.txt` so the sample report now demonstrates three real matches.
- Recheck: regenerated JSON/Markdown/HTML artifacts and confirmed non-zero counts plus excerpt cards.

## Review pass 2 — docs/comprehension
- Issue found: the README mentioned report exports in the feature list but did not show a concrete reproducible command or where the committed artifacts live.
- Fix applied: added a full report-export command, documented that `--json` can coexist with report-file outputs, and listed the committed demo artifact paths.
- Recheck: reread README usage/streaming sections against the actual CLI flags and artifact names.

## Review pass 3 — automation safety
- Issue found: there was no explicit regression coverage proving report-file side effects do not break JSON stdout, which is important for scripted artifact generation.
- Fix applied: strengthened both project-level and repo-level CLI tests so `--json` runs alongside `--report-markdown-out` and `--report-html-out`, then asserted deterministic files and stable parsed JSON across reruns.
- Recheck: project tests, repo-level tests, and the real sample export command all passed.
