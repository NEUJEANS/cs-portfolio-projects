# Review pass 1 - hyperloglog-cardinality-lab

## Checks
- read implementation for hash splitting, estimation, and merge behavior
- compared CLI output fields against portfolio usefulness
- re-ran unit tests after code changes

## Issues found
1. large-range correction could approach a `log(0)` edge if the raw estimate ever saturated the 64-bit domain
2. stats output would be easier to discuss in interviews with an integer-style estimate alongside the float

## Fixes made
- capped the large-range correction ratio before the logarithm
- added `rounded_estimate` to stats output

## Result
- tests pass after fixes
