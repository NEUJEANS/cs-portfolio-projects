# Review pass 1 — shamir authenticated bundles

## Checks
- read the updated Shamir lab implementation and CLI flow
- ran authenticated split/inspect/recover smoke commands

## Issue found
- authenticated bundles could still be recovered without any verification requirement if the CLI did not explicitly enforce a passphrase

## Fix
- made `recover` require `--auth-passphrase` whenever a bundle includes authentication metadata
- added CLI regression tests for the required-passphrase path
