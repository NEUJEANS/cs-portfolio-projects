# OR-Set vs LWW-element-set comparison — preset unobserved-remove — Unobserved remove cannot tombstone unseen tags

Replicas: a, b, c
LWW tie bias: `remove`

Story: The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=1 and remove=4 under remove-wins ties.

## Final divergence

- `notebook` — OR-Set=present, LWW=absent; OR-Set keeps only observed-remove tombstones, so active tags a:1 can survive. LWW compares add=1 vs remove=4 with remove-wins ties.

## Step-by-step comparison

| Step | Event | OR-Set view | LWW view | Divergence |
| --- | --- | --- | --- | --- |
| 1 | a adds notebook @ t=1 | elements=notebook \| active=notebook=a:1 \| tombstones=∅ | elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove | a: membership matches |
| 2 | c removes notebook @ t=4 | elements=∅ \| active=∅ \| tombstones=∅ | elements=∅ \| add_ts=∅ \| remove_ts=notebook=4 \| bias=remove | c: membership matches |
| 3 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅ \|\| b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ | a: elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove \|\| b: elements=notebook \| add_ts=notebook=1 \| remove_ts=∅ \| bias=remove | a: membership matches<br>b: membership matches |
| 4 | b ↔ c sync (both) | b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ \|\| c: elements=notebook \| active=notebook=a:1 \| tombstones=∅ | b: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove \|\| c: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove | b:notebook OR-Set=present via tags a:1; LWW=absent with add=1, remove=4, bias=remove<br>c:notebook OR-Set=present via tags a:1; LWW=absent with add=1, remove=4, bias=remove |
| 5 | a ↔ c sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅ \|\| c: elements=notebook \| active=notebook=a:1 \| tombstones=∅ | a: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove \|\| c: elements=∅ \| add_ts=notebook=1 \| remove_ts=notebook=4 \| bias=remove | a:notebook OR-Set=present via tags a:1; LWW=absent with add=1, remove=4, bias=remove<br>c:notebook OR-Set=present via tags a:1; LWW=absent with add=1, remove=4, bias=remove |

## Final OR-Set states

- `a` — elements notebook; active notebook=a:1; tombstones ∅
- `b` — elements notebook; active notebook=a:1; tombstones ∅
- `c` — elements notebook; active notebook=a:1; tombstones ∅

## Final LWW states

- `a` — elements ∅; add_ts notebook=1; remove_ts notebook=4; bias remove
- `b` — elements ∅; add_ts notebook=1; remove_ts notebook=4; bias remove
- `c` — elements ∅; add_ts notebook=1; remove_ts notebook=4; bias remove
