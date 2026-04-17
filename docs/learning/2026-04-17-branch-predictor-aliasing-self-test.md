# 2026-04-17 branch predictor aliasing self-test

## Question
If the predictor index is `(pc >> 2) & (table_size - 1)`, do these PCs collide?
- `0x100` and `0x140`
- `0x110` and `0x150`

## Check
- For `table_size = 16`:
  - `0x100 >> 2 = 0x40`, `0x140 >> 2 = 0x50`, both map to index `0x0`
  - `0x110 >> 2 = 0x44`, `0x150 >> 2 = 0x54`, both map to index `0x4`
- For `table_size = 32`:
  - `0x40 & 0x1f = 0x0`, `0x50 & 0x1f = 0x10` → no collision
  - `0x44 & 0x1f = 0x4`, `0x54 & 0x1f = 0x14` → no collision

## Result
These address pairs are a good synthetic aliasing demo because the same trace collides at 16 entries and separates cleanly at 32 entries.
