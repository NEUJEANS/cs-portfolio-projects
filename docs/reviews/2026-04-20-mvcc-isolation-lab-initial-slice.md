# MVCC isolation lab review — 2026-04-20 — initial slice

## Pass 1 — test harness / import review
- Re-ran `py_compile` and the new unit test module immediately instead of assuming a new hyphenated project path would import cleanly.
- Issue found: `tests/test_mvcc_isolation_lab.py` tried to import `projects.mvcc-isolation-lab...`, which is invalid Python syntax because of the hyphenated directory name.
- Fix: switched the test module to `importlib.util.spec_from_file_location(...)` + `sys.modules[...]` loading so the tests exercise the committed script file directly without renaming the project folder.

## Pass 2 — README semantics review
- Re-read the sample-scenario explanation after observing the repeatable-read scenario outputs across all isolation modes.
- Issue found: the README wording implied `serializable` would behave the same as `snapshot` for the reader in `repeatable_read_window.json`, but the lab's optimistic validation model intentionally aborts the reader at commit once its read set changed.
- Fix: updated `projects/mvcc-isolation-lab/README.md` so it now explains that `serializable` keeps a stable snapshot for reads but may still abort at final validation.

## Pass 3 — artifact wording / regression review
- Re-read the Markdown comparison artifacts after the serializable runs completed.
- Issue found: aborted transactions were shown with `writes ...`, which read like committed writes instead of buffered-but-rejected intent.
- Fix: updated `render_run_text()` and `render_compare_markdown()` to label aborted transaction payloads as `buffered_writes` / `buffered writes`, then added a dedicated serializable repeatable-read regression test and regenerated the committed Markdown artifacts.

## Final verification
- `python3 -m py_compile projects/mvcc-isolation-lab/mvcc_isolation_lab.py tests/test_mvcc_isolation_lab.py`
- `python3 -m unittest tests.test_mvcc_isolation_lab -v` (`10/10`)
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py validate projects/mvcc-isolation-lab/doctor_on_call.json`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/doctor_on_call.json --markdown-out docs/artifacts/mvcc-isolation-lab/doctor_on_call_compare.md`
- `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py compare projects/mvcc-isolation-lab/repeatable_read_window.json --markdown-out docs/artifacts/mvcc-isolation-lab/repeatable_read_window_compare.md`
- JSON smoke check for `repeatable_read_window.json` under `read-committed`
