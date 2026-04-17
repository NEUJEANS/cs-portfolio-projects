# Branch predictor aliasing slice wrap-up

- Timestamp: `2026-04-17T10:41:23Z`
- Primary commit: `ec7866c950dd18bc6fb02af7f4dc9e9c90e31397`

## What changed
- added an `alias-thrash` synthetic workload to `branch-predictor-lab`
- added static PC-index alias summaries to compare JSON/Markdown/SVG outputs
- extended tests for collision-group generation and table-size improvement behavior
- added research, self-test, checklist, review logs, and committed alias-thrash gallery artifacts
- updated the README, project checklist, and artifact gallery to present aliasing as a shipped feature

## Tests and reviews run
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py generate alias-thrash --branches 48 --seed 7 --output artifacts/branch-predictor-lab/alias-thrash-seed7.trace --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py compare artifacts/branch-predictor-lab/alias-thrash-seed7.trace --table-size 16 --history-bits 4 --markdown-out docs/artifacts/branch-predictor-lab/alias-thrash-comparison.md --svg-out docs/artifacts/branch-predictor-lab/alias-thrash-comparison.svg --json`
- smoke check: alias-thrash compare at table size 16 vs 32 confirmed collisions drop from `2` to `0` and simple-predictor accuracy improves
- review logs: `docs/reviews/2026-04-17-branch-predictor-aliasing-review-pass-{1,2,3}.md`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add dynamic gshare-index collision analysis or a table-size sweep report so the alias-thrash trace can show static and history-dependent interference side by side
