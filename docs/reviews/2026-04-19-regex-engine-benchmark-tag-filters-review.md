# Regex engine benchmark tag-filter review log — 2026-04-19

## Pass 1 — artifact consistency audit
- reviewed the working tree after the tag-filter implementation landed
- issue found: the built-in sample-suite artifacts were stale because the benchmark report/output format now includes tag metadata but the committed sample-suite files had not been regenerated yet
- fix applied: reran the sample-suite benchmark export so the committed Markdown/JSON artifacts reflect the current tagged benchmark contract
- reran `git diff --check` after regeneration

## Pass 2 — resumability/docs audit
- reread the regex-engine project directory against neighboring labs in this repo
- issue found: `regex-engine-lab` still lacked a dedicated `CHECKLIST.md`, which made the project less resumable than the stronger, recently maintained labs
- fix applied: added `projects/regex-engine-lab/CHECKLIST.md` with the current slice, completed slices, quality checks, and next follow-ups

## Pass 3 — tag-filter edge-case audit
- reviewed the new filter path for human-typed CLI usage rather than only clean JSON examples
- issue found: there was no regression coverage proving mixed-case or space-padded requested tags normalize correctly before filtering
- fix applied: added `test_filter_benchmark_cases_normalizes_requested_tag_whitespace_and_case` to lock in lowercase/trimmed filter handling
- reran `py_compile`, the full regex-engine-lab test suite, the sample/full/interview benchmark smoke commands, and `git diff --check`
- result: no further issues found after the normalization regression landed
