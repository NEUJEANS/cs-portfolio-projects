# external-merge-sort-lab review pass 1 - 2026-04-14

## Focus
Code-path review for correctness and memory behavior.

## Findings
- `merge_run_group` accumulated merged output in memory, which weakened the external-sort story.

## Fixes made
- changed grouped merge output to stream directly to the merged run file while still using heap-based k-way selection.
