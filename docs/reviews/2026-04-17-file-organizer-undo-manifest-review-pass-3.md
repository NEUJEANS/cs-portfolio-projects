# File organizer undo-manifest review — pass 3 — 2026-04-17

## Focus
README/demo quality and final runnable smoke checks.

## Findings
- while doing a JSON smoke test, redirecting `--json` output into a file inside the target directory caused that freshly created report file to be organized as well; this is expected shell behavior, but it is easy for a user to trip over during a demo
- README already showed the new organize and undo flows clearly, but it did not warn about the redirected-output gotcha
- final tests and smoke checks passed after writing JSON outputs outside the directory being organized

## Fixes made
- added a README tip telling users to write redirected `--json` output outside the directory being organized
- reran the end-to-end organize + undo smoke flow with manifest/output files outside the target tree

## Result
- the project docs now match the tool's real CLI behavior closely enough for a reliable portfolio walkthrough
