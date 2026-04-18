# OR-Set vs LWW-element-set comparison — preset observed-remove-sync — Observed remove yields the same final answer

Replicas: a, b, c
LWW tie bias: `remove`

Story: This script converges to the same final membership in both models; the comparison is still useful for showing that OR-Set tracks tags while LWW relies on timestamp ordering.

## Step-by-step comparison

| Step | Event | OR-Set view | LWW view | Divergence |
| --- | --- | --- | --- | --- |
| 1 | a adds notebook @ t=1 | elements=notebook \| active=notebook=a:1 \| tombstones=∅ | elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove | a: membership matches |
| 2 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅ \|\| b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ | a: elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove \|\| b: elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove | a: membership matches<br>b: membership matches |
| 3 | b removes notebook @ t=4 | elements=∅ \| active=∅ \| tombstones=a:1 | elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove | b: membership matches |
| 4 | b ↔ c sync (both) | b: elements=∅ \| active=∅ \| tombstones=a:1 \|\| c: elements=∅ \| active=∅ \| tombstones=a:1 | b: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove \|\| c: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove | b: membership matches<br>c: membership matches |
| 5 | a ↔ b sync (both) | a: elements=∅ \| active=∅ \| tombstones=a:1 \|\| b: elements=∅ \| active=∅ \| tombstones=a:1 | a: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove \|\| b: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove | a: membership matches<br>b: membership matches |
| 6 | a ↔ c sync (both) | a: elements=∅ \| active=∅ \| tombstones=a:1 \|\| c: elements=∅ \| active=∅ \| tombstones=a:1 | a: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove \|\| c: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove | a: membership matches<br>c: membership matches |

## Final OR-Set states

- `a` — elements ∅; active ∅; tombstones a:1
- `b` — elements ∅; active ∅; tombstones a:1
- `c` — elements ∅; active ∅; tombstones a:1

## Final LWW states

- `a` — elements ∅; add_ts notebook=1; remove_ts notebook=4; bias remove
- `b` — elements ∅; add_ts notebook=1; remove_ts notebook=4; bias remove
- `c` — elements ∅; add_ts notebook=1; remove_ts notebook=4; bias remove
