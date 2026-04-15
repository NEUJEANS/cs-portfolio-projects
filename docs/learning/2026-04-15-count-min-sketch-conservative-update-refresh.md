# Count-Min Sketch conservative update refresh

## Refresher
- Standard CMS update: increment every hashed bucket for the item.
- Query: estimated count is the minimum across rows.
- Conservative update: only increment hashed buckets that are currently at the item's minimum estimate.
- Why it helps: avoids needlessly raising already-inflated rows, which can reduce future overestimation.

## Quick self-test
1. **Why does CMS still avoid underestimation?**
   Because each true occurrence raises at least one minimum-tracking path enough to keep the min estimate at or above the real count.
2. **What extra merge constraint appears after this slice?**
   Sketches must share the same conservative-vs-standard update mode before merging.
3. **What cost do we pay for conservative update?**
   Slightly slower inserts because updates inspect current row values before deciding which counters to increment.
