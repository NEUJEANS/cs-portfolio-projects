# file-organizer-cli — approval quorum bundles

- **Timestamp:** 2026-04-18T08:10:59Z
- **Project:** `projects/file-organizer-cli`
- **Feature commit:** `df04ba02dcfa7d421fff15c9bd2ccbff972546c5` (`feat(file-organizer-cli): add multi-signer approval quorums`)

## What changed
- added multi-approval detached signature bundles so checksum-backed manifests can carry several trusted reviewer approvals instead of only one signer proof
- added signer-policy `approvalQuorum` support with minimum-signer and required-role enforcement so undo/verification fails closed until the approval bundle is fresh enough and complete enough for the policy
- enabled signer-policy-only verification and undo flows without a separate public-key flag by embedding the signer public key material inside each detached approval record
- fixed the end-to-end CLI workflow by allowing follow-up `--sign-manifest` runs against an existing manifest path, which lets a second reviewer append approval proof without re-running organize
- expanded tests, help text, README usage, checklist notes, review logs, and demo artifacts to cover the real multi-signer append + quorum workflow

## Tests and reviews run
- `npm test --prefix projects/file-organizer-cli`
- `npm run demo:artifacts --prefix projects/file-organizer-cli`
- `git diff --check`
- `node projects/file-organizer-cli/organizer.js --help`
- real CLI smoke: organize a temp folder, append two approvals with `node projects/file-organizer-cli/organizer.js "$tmpdir/runs/latest.json" --sign-manifest ...`, then run `--undo ... --signer-policy ...` and confirm restore succeeds with `signer quorum: 2/2 trusted approval(s); satisfied`
- review log: `docs/reviews/file-organizer-cli-2026-04-18-approval-quorum.md` (3 review passes, including a real CLI-flow fix)
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- add approval expiry or freshness windows so stale signer bundles can be rejected after a review deadline
