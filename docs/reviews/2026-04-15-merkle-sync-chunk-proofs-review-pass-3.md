# Review Pass 3 — merkle-sync-lab chunk-proof slice

## Checks
- reviewed the CLI flow from `chunk-diff --json` into `verify-chunk`
- confirmed the saved JSON payload works as a resumable artifact

## Issue found
- proof verification originally depended on in-memory objects only, which weakened the demo story for real artifact exchange

## Fix applied
- kept `verify-chunk` file-based and added a CLI test that writes `chunk-diff` output to disk before verifying a selected chunk index
