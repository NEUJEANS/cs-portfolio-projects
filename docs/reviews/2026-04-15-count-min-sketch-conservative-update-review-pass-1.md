# Review pass 1 — code path audit

## Focus
- verify conservative update semantics in `add()`
- verify merge compatibility checks include update mode
- verify serialization preserves the new option

## Findings
1. Initial collision-oriented test case did not actually demonstrate a strict improvement under the chosen deterministic mapping.
2. Core implementation correctly exposed conservative mode through config, merge validation, and JSON persistence.

## Fixes applied
- replaced the brittle collision test with a deterministic unit test that proves conservative mode increments only minimum cells while preserving the same final estimate for the updated item.

## Result
Pass complete after tightening the test to match the real algorithmic guarantee.
