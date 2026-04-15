# chang-roberts contention benchmark review — pass 1 (2026-04-15)

## Focus
API shape and benchmark usefulness.

## Checks
- Verified the new slice is a real implementation feature, not just a doc-only claim.
- Confirmed the benchmark evaluates every 1..n initiator combination on the active ring.
- Checked that single-initiator rows reuse the same simulator semantics as the original mode.

## Issue found
- The first draft summarized cheapest/most-expensive initiator sets with a `dict.get(..., fallback)` expression that still eagerly evaluated the single-initiator fallback.

## Fix applied
- Added an explicit `initiator_key(...)` helper so benchmark summaries work for both single and multi-initiator results without KeyError.
