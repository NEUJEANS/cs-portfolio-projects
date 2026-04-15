# Review pass 2 — distributed-snapshot failure/recovery slice

## Focus
Snapshot payload completeness and script output.

## Findings
- Snapshot construction could miss balances/status for processes that were down and therefore skipped during marker propagation.
- That caused incomplete snapshot state and a `KeyError` during balance adjustment.

## Fixes applied
- backfilled snapshot balances and process statuses for every process after marker traversal
- re-ran the focused test suite to confirm snapshots remain consistent with outages present
