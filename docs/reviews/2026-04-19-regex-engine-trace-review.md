# Regex engine NFA trace review log — 2026-04-19

## Pass 1 — trace accuracy audit
- checked whether the new trace timeline reported the real runtime cursor position on failed `fullmatch` runs
- issue found: the final trace step always used `len(text)` even when the active state set died earlier, which made failed traces look like they consumed more input than they actually did
- fix applied: track the last consumed position explicitly, use that position for the final closure step, and lock it down with `test_trace_fullmatch_marks_early_stop_on_failure`

## Pass 2 — docs and artifact audit
- reread the README and sample commands to make sure the new trace feature was demoable from the repo without code spelunking
- issue found: the README described tracing but did not yet point readers to committed sample outputs they could inspect immediately
- fix applied: added a dedicated trace usage section, listed the committed sample artifact files, and generated `docs/artifacts/regex-engine-lab/trace-id-fullmatch.json` plus `trace-dogs-search.json`

## Pass 3 — smoke and regression audit
- reran compile, unit, CLI trace smokes, and `git diff --check` after the fixes
- spot-checked both committed JSON trace artifacts to make sure state ordering stayed deterministic and the winning search attempt remained easy to follow
- result: no additional issues found after the pass-1 and pass-2 fixes
