# OR-Set timeline — preset observed-remove-sync — Observed remove yields the same final answer

Replicas: a, b, c

Story: Final membership ∅; active tags ∅; tombstones a:1.

| Step | Event | Details |
| --- | --- | --- |
| 1 | a adds notebook | new tag: a:1<br>elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 2 | a ↔ b sync (both) | a: elements=notebook \| active=notebook=a:1 \| tombstones=∅<br>b: elements=notebook \| active=notebook=a:1 \| tombstones=∅ |
| 3 | b removes notebook | observed tags removed: a:1<br>elements=∅ \| active=∅ \| tombstones=a:1 |
| 4 | b ↔ c sync (both) | b: elements=∅ \| active=∅ \| tombstones=a:1<br>c: elements=∅ \| active=∅ \| tombstones=a:1 |
| 5 | a ↔ b sync (both) | a: elements=∅ \| active=∅ \| tombstones=a:1<br>b: elements=∅ \| active=∅ \| tombstones=a:1 |
| 6 | a ↔ c sync (both) | a: elements=∅ \| active=∅ \| tombstones=a:1<br>c: elements=∅ \| active=∅ \| tombstones=a:1 |

## Final replica states

- `a` — elements ∅; active ∅; tombstones a:1
- `b` — elements ∅; active ∅; tombstones a:1
- `c` — elements ∅; active ∅; tombstones a:1

## Convergence

- converged: `true`
