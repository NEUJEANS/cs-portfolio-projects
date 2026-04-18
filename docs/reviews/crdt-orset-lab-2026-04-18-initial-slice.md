# crdt-orset-lab review — initial slice

Date (UTC): 2026-04-18
Project: `projects/crdt-orset-lab`

## Pass 1 — code/semantics review
- Reviewed the OR-Set merge + convergence logic against the intended distributed-systems story.
- Issue found: the initial convergence check only compared membership and active tags, which could mark replicas as converged even when tombstones/observed state still differed.
- Fix applied: changed `convergence_report()` to require full replica-state equality and added a regression test where membership matches but tombstones do not.

## Pass 2 — docs/usage audit
- Reviewed the README against the shipped CLI behavior and sample script loader.
- Issue found: the README implied only the wrapped `{ "operations": [...] }` format was accepted and did not spell out that convergence means full state equality.
- Fix applied: updated the script-format section to mention plain top-level lists and added an explicit feature bullet about full-state convergence.

## Pass 3 — portfolio/resumability audit
- Reviewed repo-level discoverability and final smoke outputs.
- Issue found: the root repo README current-progress list had not been updated with the new project, which made the slice harder to discover from the portfolio landing page.
- Fix applied: added `crdt-orset-lab` to the root `README.md`, then re-ran tests, smoke checks, `py_compile`, and `git diff --check`.

## Final verification
- Re-ran `python3 -m unittest discover -s projects/crdt-orset-lab -p 'test_*.py'` (`11/11` passing).
- Re-ran `python3 projects/crdt-orset-lab/crdt_orset_lab.py run-script --replicas a b c --script projects/crdt-orset-lab/sample_ops.json` and verified convergence plus the surviving `c:1` tag / `a:1` tombstone story.
- Re-ran `python3 -m py_compile projects/crdt-orset-lab/crdt_orset_lab.py`.
- Re-ran `git diff --check`.
- No further issues found in the final pass.
