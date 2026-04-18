# file-organizer-cli — signer policy allowlists

- **Timestamp:** 2026-04-18T07:19:57Z
- **Project:** `projects/file-organizer-cli`
- **Feature commit:** `91302930ecbcaa0a97660ab235821549881a98db` (`feat(file-organizer-cli): add signer policies`)

## What changed
- added `--signer-policy` support so checksum-backed manifest signatures can be constrained by a trusted signer allowlist instead of accepting any matching key pair
- normalized signer-policy JSON with trusted fingerprint entries plus optional reviewer `label`, `roles`, and `notes` metadata that now surfaces in apply/verify/undo reports
- kept policy-driven sign flows resumable by auto-skipping active signing inputs (manifest path, signature path, private key, signer policy, and config path) when they live inside the target directory being organized
- expanded tests for signer-policy normalization, trusted/untrusted signer enforcement, and in-target protected-path workflows
- refreshed README/checklist copy, generated demo artifacts, and added a review log plus a publishable trusted-signer policy artifact to the committed bundle

## Tests and reviews run
- `npm test --prefix projects/file-organizer-cli`
- `npm run demo:artifacts --prefix projects/file-organizer-cli`
- `git diff --check`
- real CLI smoke: organize + undo with `--signer-policy` while the private key, public key, and signer-policy file all lived inside the target directory; confirmed active signing inputs were preserved and undo verification succeeded
- review log: `docs/reviews/file-organizer-cli-2026-04-18-signer-policy.md` (3 review passes, including an artifact-path consistency fix)
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add multi-signer approval metadata or quorum rules so shared teams can require more than one trusted signer before restoring files
