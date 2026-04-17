# branch-predictor-lab review pass 8

## Focus
Regression-test audit for the new predictor CLI surface.

## Issue found
The test suite covered `compare` and synthetic-trace generation, but it did not directly exercise `simulate --predictor local-history` or `simulate --predictor tournament`. That left the new JSON-facing state snapshots unguarded.

## Fix applied
- added a CLI regression test for `simulate --predictor local-history --json`
- added a CLI regression test for `simulate --predictor tournament --json`
- asserted advanced final-state fields like `trained_patterns`, `chooser_table`, and nested local/global predictor snapshots

## Result
The advanced predictor CLI surface is now covered end-to-end instead of relying only on internal API tests.
