# merkle-sync-lab Review Pass 5 — test coverage audit

## Focus
- re-read the test suite after adding the `plan` subcommand
- looked for regressions where earlier diff/build behavior might silently lose coverage
- checked machine-readable output expectations

## Issue found
- the first draft of the CLI integration test only exercised `build` + `plan`, which weakened explicit coverage for `diff --json`

## Fix applied
- expanded the CLI integration test to validate `build`, `diff --json`, and `plan --json` in one flow
- verified the updated target file correctly produces an `update` operation in the generated sync plan
