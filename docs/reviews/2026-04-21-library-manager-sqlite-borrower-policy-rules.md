# library-manager-sqlite borrower policy rules review log

Date: 2026-04-21

## Review pass 1, compatibility with older tests and flows
- After the first enforcement pass, existing history coverage broke because the new default overdue block prevented an intentionally overdue borrower from checking out another book inside an older test scenario.
- Fix: updated the test fixture to explicitly disable the overdue block only for that scenario, so legacy history coverage still validates the intended report behavior without weakening the new default policy.

## Review pass 2, status-language clarity and edge-case pressure
- Re-read the policy report wording and noticed the raw internal statuses were too implementation-flavored for a portfolio artifact.
- Also spotted an edge case where a borrower with zero active loans could have been labeled `one slot remaining` when the configured limit was `1`, which sounds like pressure even though nothing is currently checked out.
- Fix: added human-facing `status_label` strings like `blocked by overdue items` and `one slot remaining`, reused them in both the plain-text output and the Markdown/HTML exports, and tightened the `at-limit` classification so it only appears when the borrower already has at least one active loan.

## Review pass 3, validation and artifact determinism
- Re-ran `py_compile`, the full unittest suite, a real `policy` CLI export to the committed sample Markdown and HTML artifacts, and a second deterministic rerun diff check.
- Confirmed the sample exports stayed byte-for-byte stable across reruns and that `git diff --check` remained clean after the fixes.
