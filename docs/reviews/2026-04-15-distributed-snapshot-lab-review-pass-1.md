# Review Pass 1 - Distributed Snapshot Lab

## Focus
- parser correctness
- CLI input shape

## Findings
1. `parse_transfer` unpacked colon-separated fields incorrectly and rejected valid inputs like `A:B:3:rent`.

## Fixes applied
- rewrote `parse_transfer` to require exactly four fields and return sender, receiver, amount, and label directly
- reran the project test suite after the fix
