# Review Pass 1 — Suffix Automaton Lab

## Checks
- inspected state extension and clone handling logic
- verified substring count propagation approach against suffix automaton invariants
- reviewed README examples against CLI flags

## Issue found
- `longest_repeated_substring` accepted thresholds below `2`, which would blur the meaning of “repeated” and return surprising results.

## Fix applied
- added validation so thresholds below `2` raise a clear error
- covered the validation path with an automated test
