# Regex engine combined showcase review log — 2026-04-19

## Pass 1 — portfolio-story audit
- reviewed the planned showcase against the current README follow-up and the committed artifact set
- issue found: a page that merely listed trace files beside benchmark dashboards would still leave the reviewer to mentally connect which benchmark suites reused the same regex case
- fix applied: matched trace `pattern` + `mode` pairs against benchmark `case_definitions` and added related-dashboard links directly on each trace card

## Pass 2 — portability/resumability audit
- reread the new showcase generator with a failure-focused lens around where the output file might live
- issue found: hard-coded same-directory assumptions would make the generated page fragile if the output path changed or a future cron run wrote the page from a nearby docs directory
- fix applied: added explicit artifact-path building plus relative-link generation from `--html-out` so the showcase stays repo-portable instead of relying on absolute paths

## Pass 3 — regression/docs audit
- reviewed the final tree for whether a later cron run could discover and safely rebuild the feature
- issue found: without explicit regression coverage and docs updates, the new command would be easy to break or forget even if the first generated HTML looked correct
- fix applied: added showcase path/report/HTML/CLI tests, generated the committed `docs/artifacts/regex-engine-lab/showcase.html` artifact, and updated the README plus checklist/research/learning notes
- reran `python3 -m py_compile`, `python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py'`, the real `showcase-demo` smoke command, and `git diff --check`
- result: no further issues found after linking, portability, docs, and regression coverage were updated together
