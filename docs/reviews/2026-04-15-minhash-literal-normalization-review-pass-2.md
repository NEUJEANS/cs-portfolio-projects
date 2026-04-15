# Review pass 2 — MinHash literal normalization

## Checks
- Manual CLI smoke test for `compare`, `build-index`, and `benchmark` with `--token-mode code --normalize-literals`
- Verified Markdown benchmark export includes `Normalize literals: True`

## Findings
- Constant-only code changes now collapse into identical code shingles when literal normalization is enabled.
- CLI JSON payloads expose `normalize_literals` consistently across commands.
- Saved index metadata records the new flag for resumable follow-up scans.

## Fixes made
- None after this pass.
