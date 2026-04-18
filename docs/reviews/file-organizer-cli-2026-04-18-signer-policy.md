# file-organizer-cli signer-policy review log

## Review pass 1 — test + artifact regression sweep
- Ran `npm test --prefix projects/file-organizer-cli`.
- Ran `npm run demo:artifacts --prefix projects/file-organizer-cli`.
- Ran `git diff --check`.
- Result: core signer-policy implementation, report formatting, and generated demo artifacts were green.

## Review pass 2 — docs/artifact consistency review
- Reviewed the README diff plus generated `demo-summary.md`, `demo-apply-report.txt`, `demo-signature-verify.txt`, and `demo-undo-report.txt`.
- Found and fixed one artifact consistency issue: the generated signer-policy file path inside proof output was sanitized as `/demo/file-organizer-cli/trusted-signers.json` while the published artifact name was `demo-trusted-signers.json`.
- Fix: renamed the generated policy file to `demo-trusted-signers.json` so the proof output and committed artifact bundle tell the same story.

## Review pass 3 — real CLI smoke with in-target signing inputs
- Created an isolated temp folder containing:
  - files to organize
  - `buckets.json`
  - `keys/team.pem`
  - `keys/team.pub.pem`
  - `keys/trusted-signers.json`
  - `runs/latest.json`
- Ran:
  - `node projects/file-organizer-cli/organizer.js "$tmpdir" --config "$tmpdir/buckets.json" --manifest-out "$tmpdir/runs/latest.json" --manifest-checksum --sign-manifest "$tmpdir/keys/team.pem" --signer-policy "$tmpdir/keys/trusted-signers.json"`
  - `node projects/file-organizer-cli/organizer.js --undo "$tmpdir/runs/latest.json" --verify-manifest-signature "$tmpdir/keys/team.pub.pem" --signature-path "$tmpdir/runs/latest.json.sig.json" --signer-policy "$tmpdir/keys/trusted-signers.json"`
- Verified:
  - organize succeeds with the private key and signer-policy files stored inside the target tree
  - the key and policy files remain in place because active signing inputs are auto-skipped
  - undo succeeds with signer-policy verification and restores the original files
- One manual invocation typo was caught and corrected during review (`latest.sig.json` vs the actual default `latest.json.sig.json`); the corrected smoke run passed cleanly.
