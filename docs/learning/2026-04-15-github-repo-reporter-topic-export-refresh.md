# 2026-04-15 GitHub repo reporter topic/export refresh

## Quick refresh
- GitHub's repository list REST endpoints for users and orgs expose a `topics` array in the minimal repository payload, so a topic breakdown can be computed without per-repo follow-up requests.
- For a small Node CLI, writing output should create parent directories first to make `--out reports/foo.md` work reliably.
- Keeping fetch, summarize, format, and write phases separate makes the CLI easier to test and safer to extend.

## Self-test
- If report generation prints to stdout and also writes via `--out`, the write path should reuse the already-formatted output instead of reformatting.
- A missing value after `--out` should fail early with a clear CLI error.
- Topic counts should count repo presence, not individual tag occurrences inside a single repo object.
