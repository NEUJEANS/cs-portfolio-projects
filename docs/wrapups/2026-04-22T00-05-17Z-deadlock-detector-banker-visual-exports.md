# deadlock-detector-lab Banker visual exports

- Timestamp: 2026-04-22T00:05:17Z
- Feature commit: `04b606e` (`feat(deadlock-detector-lab): add banker visual exports`)

## What changed
- added first-class Banker safety SVG and HTML exports plus dedicated request-trial SVG and HTML exports
- embedded the new Banker visuals inside the combined detection-vs-avoidance dashboard HTML so the avoidance half is screenshot-friendly too
- refreshed the deadlock-detector README, checklist history, and slice-specific research, learning, and review notes
- committed deterministic sample Banker SVG/HTML artifacts under `docs/artifacts/deadlock-detector-lab/`

## Tests and checks
- `python3 -m py_compile projects/deadlock-detector-lab/deadlock_detector.py projects/deadlock-detector-lab/test_deadlock_detector.py`
- `python3 -m unittest -v projects/deadlock-detector-lab/test_deadlock_detector.py`
- real artifact-generation smoke for `analyze-banker`, `request-banker`, and `dashboard` outputs
- deterministic rerun checks with `cmp` across JSON, Markdown, SVG, and HTML exports
- `git diff --check`
- `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Review passes
1. added explicit question framing to the request visual so it stands alone
2. removed empty SVG spacer text nodes from multiline rendering
3. changed the request metric label to `Trial available` vs `Current available` depending on whether a trial allocation exists

## Next step
- add an unsafe-request sample artifact set so the portfolio shows both the granted and denied Banker paths side by side
