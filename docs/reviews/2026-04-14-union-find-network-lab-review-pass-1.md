# Review pass 1 — union-find-network-lab

## Focus
Implementation correctness and failure handling.

## Findings
- The first draft assumed script input was always a list of `{op, args}` objects.
- Malformed input would have raised raw Python type/key errors instead of clear user-facing validation errors.

## Fixes made
- Added explicit validation for script container type, required `op`, and list-typed `args`.
- Added regression tests for malformed script input.
