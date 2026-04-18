# OR-Set timeline — script sample_ops.json

Replicas: a, b, c

Story: Observed-remove story: a remove tombstones only the add-tags a replica has already observed, so membership still survives via notebook=c:1 while tombstones retain a:1.

| Step | Event | Details |
| --- | --- | --- |
| 1 | a adds notebook | new tag: a:1<br>elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 2 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅<br>b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 3 | b removes notebook | observed tags removed: a:1<br>elements=∅ \| active=∅ \| tombstones=a:1 |
| 4 | c adds notebook | new tag: c:1<br>elements=notebook \| active=notebook=c:1 \| tombstones=∅ |
| 5 | c ↔ a sync (both) | c: elements=notebook \| active=notebook=a:1, c:1 \| tombstones=∅<br>a: elements=notebook \| active=notebook=a:1, c:1 \| tombstones=∅ |
| 6 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=c:1 \| tombstones=a:1<br>b: elements=notebook \| active=notebook=c:1 \| tombstones=a:1 |
| 7 | a ↔ c sync (both) | a: elements=notebook \| active=notebook=c:1 \| tombstones=a:1<br>c: elements=notebook \| active=notebook=c:1 \| tombstones=a:1 |

## Final replica states

- `a` — elements notebook; active notebook=c:1; tombstones a:1
- `b` — elements notebook; active notebook=c:1; tombstones a:1
- `c` — elements notebook; active notebook=c:1; tombstones a:1

## Convergence

- converged: `true`
