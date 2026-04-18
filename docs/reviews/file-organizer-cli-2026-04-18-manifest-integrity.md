# file-organizer-cli review log — 2026-04-18 manifest integrity slice

## Scope
Added checksum-backed manifest support, automatic verification during undo, docs/demo updates, and regression coverage.

## Review pass 1 — API / integrity model
- Checked `organizer.js` integrity helpers and undo flow for consistent result shapes.
- Issue found: `verifyManifestIntegrity()` returned a different object shape when no checksum metadata existed.
- Fix applied: added `reason: null` to the no-integrity path and added a regression assertion in the manifest test.

## Review pass 2 — CLI guard coverage
- Checked flag interactions in `parseArgs()` and corresponding tests.
- Issue found: the explicit `--undo ... --manifest-checksum` guard existed in code but did not have its own regression assertion.
- Fix applied: added a parse-args test that rejects `--manifest-checksum` during undo flows.

## Review pass 3 — README / artifact alignment
- Compared the README bundle list and examples against the regenerated demo artifacts and real `--help` output.
- Issue found: the README bundle list omitted `demo-restored-tree.txt`, even though the generator publishes it.
- Fix applied: added the restored-tree artifact to the README bundle list and updated docs to mention checksum-backed manifests plus verified undo reports.

## Validation rerun after fixes
- `npm test`
- `npm run demo:artifacts`
- `git diff --check`
