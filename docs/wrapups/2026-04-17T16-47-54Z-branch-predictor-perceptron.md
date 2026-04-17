# Branch predictor perceptron slice wrap-up

- Timestamp: `2026-04-17T16:47:54Z`
- Primary commit: `886af994116821215ab6b68ba3c1250ee2e7b98b`

## What changed
- added a `perceptron` predictor to `projects/branch-predictor-lab/branch_predictor.py` and wired it into the compare/simulate CLI flows
- added a reproducible `perceptron-majority` synthetic workload plus tests that prove the perceptron beats the classic table-based baselines on the committed long-history configuration
- updated the project README/checklists and added perceptron-specific research, refresh/self-test, and review docs so the slice is resumable
- generated and committed `perceptron-majority` gallery artifacts under `artifacts/branch-predictor-lab/` and `docs/artifacts/branch-predictor-lab/`, then linked them from the artifact gallery index

## Tests and reviews run
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py generate perceptron-majority --branches 96 --seed 13 --output artifacts/branch-predictor-lab/perceptron-majority-seed13.trace --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py compare artifacts/branch-predictor-lab/perceptron-majority-seed13.trace --table-size 32 --history-bits 12 --markdown-out docs/artifacts/branch-predictor-lab/perceptron-majority-comparison.md --svg-out docs/artifacts/branch-predictor-lab/perceptron-majority-comparison.svg --json`
- smoke check: `compare` confirmed `perceptron` is the best predictor on the committed trace/config pair and the SVG parses cleanly as XML
- review logs: `docs/reviews/2026-04-17-branch-predictor-perceptron-review-pass-{1,2,3}.md`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add perceptron threshold/weight-limit sweep commands or artifact reports so the neural slice has the same parameter-exploration depth that alias-thrash already gives table-size trade-off demos
