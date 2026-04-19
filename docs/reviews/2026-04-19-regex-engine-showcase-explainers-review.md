# Regex engine showcase explainer review log — 2026-04-19

## Pass 1 — wording/portfolio audit
- reviewed the generated showcase HTML from a recruiter-skimming perspective
- issue found: the feature summary rendered `5 classs`, which made the new explainer section look sloppy even though the metrics were correct
- fix applied: used an explicit irregular plural (`class` -> `classes`) in the showcase count formatter and added an HTML assertion that locks the corrected wording into tests

## Pass 2 — robustness audit
- reread the explainer HTML assembly looking for output that would degrade badly on future patterns
- issue found: the NFA summary assumed an accept-state index always exists and would have printed `accept #None` for malformed or future partial payloads
- fix applied: added `_format_accept_state_label(...)` so showcase wording fails soft with `accept state unavailable` instead of emitting broken UI text

## Pass 3 — resumability/regression audit
- checked whether the repo would clearly advertise that the showcase now includes explainers and whether later cron runs could safely rebuild it
- issue found: the README/checklist still described AST/NFA explainers as a future improvement, so the repo narrative lagged behind the dirty implementation
- fix applied: updated README + checklist, regenerated the committed showcase artifact, and tightened tests around explainer counts/story text/HTML wording
- reran `python3 -m py_compile`, `python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py'`, `python3 projects/regex-engine-lab/regex_engine_lab.py showcase-demo --html-out docs/artifacts/regex-engine-lab/showcase.html --artifact-dir docs/artifacts/regex-engine-lab`, and `git diff --check`
- result: no further issues found after wording, robustness, docs, and regression coverage were refreshed together
