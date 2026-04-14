# Review pass 3: lsm-tree-kv

## Focus
Edge-case correctness around deletes and compaction.

## Findings
- The suite did not explicitly cover the case where compaction should remove all data because only tombstones remain.
- Without that check, a regression could leave empty/stale SSTables behind.

## Fixes applied
- added a dedicated test for compacting a store whose keys have all been deleted
- verified that the resulting store reports zero live keys and zero SSTables
- confirmed the project remains green under `unittest`
