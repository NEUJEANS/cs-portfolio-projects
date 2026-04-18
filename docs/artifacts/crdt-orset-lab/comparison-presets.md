# OR-Set comparison preset suite

2 preset(s) finish with different OR-Set vs LWW membership, while 1 preset(s) agree on the final answer. Together they make it easier to explain when observed-remove tags matter and when timestamp ordering is enough.

| Preset | Outcome | OR-Set final membership | LWW final membership | Notes |
| --- | --- | --- | --- | --- |
| `concurrent-readd` | diverge | a=notebook; b=notebook; c=notebook | a=∅; b=∅; c=∅ | The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=4 and remove=5 under remove-wins ties. |
| `unobserved-remove` | diverge | a=notebook; b=notebook; c=notebook | a=∅; b=∅; c=∅ | The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=1 and remove=4 under remove-wins ties. |
| `observed-remove-sync` | align | a=∅; b=∅; c=∅ | a=∅; b=∅; c=∅ | This script converges to the same final membership in both models; the comparison is still useful for showing that OR-Set tracks tags while LWW relies on timestamp ordering. |

## Scenario notes

### Concurrent re-add survives in OR-Set (`concurrent-readd`)

- script: `sample_compare_ops.json`
- LWW tie bias: `remove`
- description: Replica b removes only the tag it observed, while replica c later adds the same element with a fresh tag. OR-Set keeps the new tag after sync, but remove-wins LWW drops the element because the later remove timestamp still dominates.
- story: The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=4 and remove=5 under remove-wins ties.
- OR-Set final membership: a=notebook; b=notebook; c=notebook
- LWW final membership: a=∅; b=∅; c=∅
- divergence notes:
  - `notebook` — OR-Set=present, LWW=absent; OR-Set keeps only observed-remove tombstones, so active tags c:1 can survive. LWW compares add=4 vs remove=5 with remove-wins ties.

### Unobserved remove cannot tombstone unseen tags (`unobserved-remove`)

- script: `presets/unobserved-remove.json`
- LWW tie bias: `remove`
- description: Replica c issues a remove before it has ever observed a's add. The OR-Set remove is effectively empty, but LWW still records a later remove timestamp that suppresses the earlier add once replicas merge.
- story: The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=1 and remove=4 under remove-wins ties.
- OR-Set final membership: a=notebook; b=notebook; c=notebook
- LWW final membership: a=∅; b=∅; c=∅
- divergence notes:
  - `notebook` — OR-Set=present, LWW=absent; OR-Set keeps only observed-remove tombstones, so active tags a:1 can survive. LWW compares add=1 vs remove=4 with remove-wins ties.

### Observed remove yields the same final answer (`observed-remove-sync`)

- script: `presets/observed-remove-sync.json`
- LWW tie bias: `remove`
- description: Replica b first syncs the add and then removes the element, so both models agree on the final absence. This preset is a useful control case beside the divergence-heavy scenarios.
- story: This script converges to the same final membership in both models; the comparison is still useful for showing that OR-Set tracks tags while LWW relies on timestamp ordering.
- OR-Set final membership: a=∅; b=∅; c=∅
- LWW final membership: a=∅; b=∅; c=∅
- divergence notes: none; both models converge to the same final membership here.

