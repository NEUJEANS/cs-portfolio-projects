# Branch-predictor-lab review — pass 2

## Focus
Validation coverage and failure-mode confidence.

## Issue found
- The test suite covered happy-path predictor behavior, but it did not assert that invalid predictor-table sizes fail fast. That left a small but important configuration guard unverified.

## Fix applied
- Added `test_build_predictor_rejects_non_power_of_two_table_size` to lock in the power-of-two validation path.
- Re-ran the targeted pytest file after the test addition.

## Result
- The lab now has explicit coverage for a common configuration mistake instead of relying on manual inspection.
