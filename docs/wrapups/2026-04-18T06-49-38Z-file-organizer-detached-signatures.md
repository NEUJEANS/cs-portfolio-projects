# file-organizer-cli — detached manifest signatures

- **Timestamp:** 2026-04-18T06:49:38Z
- **Project:** `projects/file-organizer-cli`
- **Feature commit:** `131b263ab82f517e7f49dba35c0c062929ea9073` (`feat(file-organizer-cli): add detached manifest signatures`)

## What changed
- added detached-signature support for checksum-backed organize manifests via `--sign-manifest` and optional `--signature-path`
- added undo-time signer verification via `--verify-manifest-signature`, so teams can require both manifest integrity and authorship before restoring files
- tightened the signing workflow so detached signatures require checksum-backed manifest metadata instead of silently signing unhashed manifests
- expanded regression coverage for signature preconditions, detached-signature generation/verification, and signature-verified undo flows
- refreshed the README, project checklists, review log, and committed demo artifact bundle with a detached signature sidecar, published public key, and signature-verification proof

## Tests and reviews run
- `npm test --prefix projects/file-organizer-cli`
- `npm run demo:artifacts --prefix projects/file-organizer-cli`
- `git diff --check`
- real temp-dir smoke: generate an Ed25519 keypair, run `organizer.js` with `--manifest-checksum --sign-manifest`, then run `--undo --verify-manifest-signature` and confirm both files restore plus the detached sidecar exists
- review log: `docs/reviews/file-organizer-cli-2026-04-18-detached-signatures.md` (3 review passes + validation rerun)
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add signer-policy helpers such as trusted fingerprint allowlists or multi-signer approval metadata for shared team workflows
