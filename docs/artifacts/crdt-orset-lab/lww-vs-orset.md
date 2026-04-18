# OR-Set vs LWW-element-set comparison — script sample_compare_ops.json

Replicas: a, b, c
LWW tie bias: `remove`

Story: The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=4 and remove=5 under remove-wins ties.

## Final divergence

- `notebook` — OR-Set=present, LWW=absent; OR-Set keeps only observed-remove tombstones, so active tags c:1 can survive. LWW compares add=4 vs remove=5 with remove-wins ties.

## Step-by-step comparison

| Step | Event | OR-Set view | LWW view | Divergence |
| --- | --- | --- | --- | --- |
| 1 | a adds notebook @ t=1 | elements=notebook \| active=notebook=a:1 \| tombstones=∅ | elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove | a: membership matches |
| 2 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅ \|\| b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ | a: elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove \|\| b: elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove | a: membership matches<br>b: membership matches |
| 3 | b removes notebook @ t=5 | elements=∅ \| active=∅ \| tombstones=a:1 | elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=5 \| bias=remove | b: membership matches |
| 4 | c adds notebook @ t=4 | elements=notebook \| active=notebook=c:1 \| tombstones=∅ | elements=notebook \| add_ts=notebook=4 \| remove_ts=∅ \| bias=remove | c: membership matches |
| 5 | c ↔ a sync (both) | c: elements=notebook \| active=notebook=a:1, c:1 \| tombstones=∅ \|\| a: elements=notebook \| active=notebook=a:1, c:1 \| tombstones=∅ | c: elements=notebook \| add_ts=notebook=4 \| remove_ts=∅ \| bias=remove \|\| a: elements=notebook \| add_ts=notebook=4 \| remove_ts=∅ \| bias=remove | c: membership matches<br>a: membership matches |
| 6 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=c:1 \| tombstones=a:1 \|\| b: elements=notebook \| active=notebook=c:1 \| tombstones=a:1 | a: elements=∅ \| add_ts=notebook=4 \| remove_ts=notebook=5 \| bias=remove \|\| b: elements=∅ \| add_ts=notebook=4 \| remove_ts=notebook=5 \| bias=remove | a:notebook OR-Set=present via tags c:1; LWW=absent with add=4, remove=5, bias=remove<br>b:notebook OR-Set=present via tags c:1; LWW=absent with add=4, remove=5, bias=remove |
| 7 | a ↔ c sync (both) | a: elements=notebook \| active=notebook=c:1 \| tombstones=a:1 \|\| c: elements=notebook \| active=notebook=c:1 \| tombstones=a:1 | a: elements=∅ \| add_ts=notebook=4 \| remove_ts=notebook=5 \| bias=remove \|\| c: elements=∅ \| add_ts=notebook=4 \| remove_ts=notebook=5 \| bias=remove | a:notebook OR-Set=present via tags c:1; LWW=absent with add=4, remove=5, bias=remove<br>c:notebook OR-Set=present via tags c:1; LWW=absent with add=4, remove=5, bias=remove |

## Final OR-Set states

- `a` — elements notebook; active notebook=c:1; tombstones a:1
- `b` — elements notebook; active notebook=c:1; tombstones a:1
- `c` — elements notebook; active notebook=c:1; tombstones a:1

## Final LWW states

- `a` — elements ∅; add_ts notebook=4; remove_ts notebook=5; bias remove
- `b` — elements ∅; add_ts notebook=4; remove_ts notebook=5; bias remove
- `c` — elements ∅; add_ts notebook=4; remove_ts notebook=5; bias remove
