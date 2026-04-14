# Review Pass 1 — consistent-hashing-lab

## Checks
- ran unit tests
- manually inspected distribution and remap JSON output
- reviewed whether defaults produce portfolio-friendly results

## Issue found
- The initial default of 32 virtual nodes was serviceable but produced more skew than needed for a demo.

## Fix applied
- Increased the default virtual node count to 128 in code, tests, and README examples to improve default balance.
