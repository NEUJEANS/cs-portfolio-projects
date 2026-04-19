# Regex engine benchmark review log — 2026-04-19

## Pass 1 — JSON/publishability audit
- reviewed the new benchmark report payload and markdown rendering path for values that could become awkward once artifacts are committed or consumed elsewhere
- issue found: the timing helper could theoretically emit non-standard JSON `Infinity` for `ops_per_second` if an extremely tiny run measured as zero elapsed time
- fix applied: switched zero-elapsed `ops_per_second` to `null` and made Markdown rendering show `n/a` instead of assuming a float

## Pass 2 — docs/benchmark-contract audit
- reread the README benchmark section against the engine's deliberate ASCII-only shorthand-class behavior
- issue found: the new benchmark docs did not make the ASCII-only sample-suite choice explicit enough, which could confuse reviewers who know Python `re` defaults to Unicode-aware shorthand classes
- fix applied: added a direct README note that the built-in benchmark suite stays ASCII-only on purpose so parity checks stay semantically fair

## Pass 3 — regression + smoke audit
- reran `py_compile`, the full regex-engine-lab unit/CLI suite, the sample-suite benchmark artifact generation command, a single-case benchmark smoke, and `git diff --check`
- checked the committed Markdown artifact to confirm the updated benchmark table still rendered cleanly after the pass-1 change
- result: no additional issues found after the earlier fixes
