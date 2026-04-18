# OR-Set timeline — preset unobserved-remove — Unobserved remove cannot tombstone unseen tags

Replicas: a, b, c

Story: Final membership notebook; active tags notebook=a:1; tombstones ∅.

| Step | Event | Details |
| --- | --- | --- |
| 1 | a adds notebook | new tag: a:1<br>elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 2 | c removes notebook | observed tags removed: ∅<br>elements=∅ \| active=∅ \| tombstones=∅ |
| 3 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅<br>b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 4 | b ↔ c sync (both) | b: elements=notebook \| active=notebook=a:1 \| tombstones=∅<br>c: elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 5 | a ↔ c sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅<br>c: elements=notebook \| active=notebook=a:1 \| tombstones=∅ |

## Final replica states

- `a` — elements notebook; active notebook=a:1; tombstones ∅
- `b` — elements notebook; active notebook=a:1; tombstones ∅
- `c` — elements notebook; active notebook=a:1; tombstones ∅

## Convergence

- converged: `true`
