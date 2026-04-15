# 2026-04-15 MinHash incremental refresh

## Quick refresh
- Reuse is safest when the persisted artifact includes a stable content fingerprint, not just mtimes or file sizes.
- Keeping refresh logic at the `IndexedDocument` level avoids accidental metadata drift between full builds and refresh builds.
- For resumable CLI workflows, preserving the original index parameters (`glob`, shingle size, hash count, band count, seed) matters as much as preserving the signatures.

## Self-test
- Confirmed unchanged files can keep the exact prior `IndexedDocument` entry.
- Confirmed changed files recompute signatures using the same index parameters.
- Confirmed removed files drop out of the refreshed index instead of lingering as stale candidates.
