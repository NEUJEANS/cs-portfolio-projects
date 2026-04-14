# Review pass 2 - hyperloglog-cardinality-lab

## Checks
- reviewed CLI argument behavior and invalid-input handling
- checked simulation helpers for deterministic and failing cases
- re-ran unit tests after code changes

## Issues found
1. `merge` accepted a single sketch path even though the command is intended for combining sketches
2. simulation error paths were not explicitly covered by tests

## Fixes made
- made `merge` fail fast unless at least two sketches are provided
- added unit tests for invalid simulation sizes

## Result
- tests pass after fixes
