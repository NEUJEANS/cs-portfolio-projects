# Consistent Hashing Replication Review — 2026-04-14

## Pass 1 — API and data-model review
Findings:
- Initial replication upgrade exposed only the requested replication factor, which could be misleading when it exceeded available nodes.
- Replica-selection validation depended on runtime logic instead of parser-level argument checks.

Fixes applied:
- Added `effective_replication_factor(...)` and surfaced it in reports/remap output.
- Added `positive_int` CLI validation for `--virtual-nodes` and `--replication-factor`.

## Pass 2 — behavior and edge-case review
Findings:
- Remap output only counted keys with changed replica sets, but did not quantify total replica-placement churn.
- Needed explicit regression coverage for capped replication-factor behavior.

Fixes applied:
- Added `replica_placement_changes` to remap output.
- Added tests for capped replication factor and related report totals.

## Pass 3 — docs and UX review
Findings:
- README needed to explain distinct-node replica selection and capped effective replication.
- Needed a clear example showing replication-aware remap output.

Fixes applied:
- Expanded README feature list and notes.
- Added replication-aware `assign`, `report`, and `remap` usage examples.

## Validation rerun
- `python3 -m unittest projects/consistent-hashing-lab/test_consistent_hashing.py`
- manual CLI smoke tests for `report` with replication, capped replication, and `remap` with replication
