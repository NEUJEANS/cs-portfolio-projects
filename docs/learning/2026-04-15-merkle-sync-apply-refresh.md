# 2026-04-15 merkle-sync apply refresh

## Quick refresh
- `shutil.copy2()` preserves file metadata and is a better fit than plain text rewrites for a sync tool demo.
- `Path.unlink()` is enough for file deletions in this project because plans only target file paths, not directory removals.
- A dry-run/apply split keeps the CLI safe and portfolio-friendly while still demonstrating real filesystem execution.
- If the source input is only a saved manifest, execution should be rejected because the content bytes needed for copy/update are unavailable.

## Self-test
1. If the plan includes `mkdir docs`, `copy docs/a.txt`, `update config.json`, and `delete stale.log`, the operation order should create parents before file writes and delete stale files last.
2. `apply --execute` should copy bytes from the live source tree into the target, while plain `apply` should leave the target untouched.
3. Executing from a manifest-only source should fail fast with a clear error instead of pretending the plan is executable.

## Expected answers
1. Yes — parent directories first, file materialization next, deletes last.
2. Yes — dry-run reports only planned operations; execute performs them.
3. Yes — require a live source directory for execution.
