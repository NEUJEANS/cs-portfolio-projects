# OR-Set comparison preset suite

2 preset(s) finish with different OR-Set vs LWW membership, while 1 preset(s) agree on the final answer. Together they make it easier to explain when observed-remove tags matter and when timestamp ordering is enough.

| Preset | Outcome | OR-Set final membership | LWW final membership | Notes | Artifacts |
| --- | --- | --- | --- | --- | --- |
| `concurrent-readd` | diverge | a=notebook; b=notebook; c=notebook | a=∅; b=∅; c=∅ | The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=4 and remove=5 under remove-wins ties. | [bundle](comparison-presets/concurrent-readd/index.html) · [zip](comparison-presets/concurrent-readd/concurrent-readd-bundle.zip) · [comparison](comparison-presets/concurrent-readd/comparison.html) · [timeline](comparison-presets/concurrent-readd/timeline.html) · [replay](comparison-presets/concurrent-readd/replay.html) · [anti-entropy](comparison-presets/concurrent-readd/anti-entropy.html) · [snapshot](comparison-presets/concurrent-readd/orset-snapshot.json) |
| `unobserved-remove` | diverge | a=notebook; b=notebook; c=notebook | a=∅; b=∅; c=∅ | The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=1 and remove=4 under remove-wins ties. | [bundle](comparison-presets/unobserved-remove/index.html) · [zip](comparison-presets/unobserved-remove/unobserved-remove-bundle.zip) · [comparison](comparison-presets/unobserved-remove/comparison.html) · [timeline](comparison-presets/unobserved-remove/timeline.html) · [replay](comparison-presets/unobserved-remove/replay.html) · [anti-entropy](comparison-presets/unobserved-remove/anti-entropy.html) · [snapshot](comparison-presets/unobserved-remove/orset-snapshot.json) |
| `observed-remove-sync` | align | a=∅; b=∅; c=∅ | a=∅; b=∅; c=∅ | This script converges to the same final membership in both models; the comparison is still useful for showing that OR-Set tracks tags while LWW relies on timestamp ordering. | [bundle](comparison-presets/observed-remove-sync/index.html) · [zip](comparison-presets/observed-remove-sync/observed-remove-sync-bundle.zip) · [comparison](comparison-presets/observed-remove-sync/comparison.html) · [timeline](comparison-presets/observed-remove-sync/timeline.html) · [replay](comparison-presets/observed-remove-sync/replay.html) · [anti-entropy](comparison-presets/observed-remove-sync/anti-entropy.html) · [snapshot](comparison-presets/observed-remove-sync/orset-snapshot.json) |

## Scenario notes

### Concurrent re-add survives in OR-Set (`concurrent-readd`)

- script: `sample_compare_ops.json`
- LWW tie bias: `remove`
- description: Replica b removes only the tag it observed, while replica c later adds the same element with a fresh tag. OR-Set keeps the new tag after sync, but remove-wins LWW drops the element because the later remove timestamp still dominates.
- story: The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=4 and remove=5 under remove-wins ties.
- OR-Set final membership: a=notebook; b=notebook; c=notebook
- LWW final membership: a=∅; b=∅; c=∅
- detail bundle directory: `comparison-presets/concurrent-readd`
- direct artifacts: [bundle](comparison-presets/concurrent-readd/index.html) · [zip](comparison-presets/concurrent-readd/concurrent-readd-bundle.zip) · [comparison](comparison-presets/concurrent-readd/comparison.html) · [timeline](comparison-presets/concurrent-readd/timeline.html) · [replay](comparison-presets/concurrent-readd/replay.html) · [anti-entropy](comparison-presets/concurrent-readd/anti-entropy.html) · [snapshot](comparison-presets/concurrent-readd/orset-snapshot.json)
- companion files: [timeline.md](comparison-presets/concurrent-readd/timeline.md) · [timeline.mmd](comparison-presets/concurrent-readd/timeline.mmd) · [timeline.svg](comparison-presets/concurrent-readd/timeline.svg) · [comparison.md](comparison-presets/concurrent-readd/comparison.md) · [comparison.json](comparison-presets/concurrent-readd/comparison.json) · [anti-entropy.md](comparison-presets/concurrent-readd/anti-entropy.md) · [anti-entropy.json](comparison-presets/concurrent-readd/anti-entropy.json)
- divergence notes:
  - `notebook` — OR-Set=present, LWW=absent; OR-Set keeps only observed-remove tombstones, so active tags c:1 can survive. LWW compares add=4 vs remove=5 with remove-wins ties.

### Unobserved remove cannot tombstone unseen tags (`unobserved-remove`)

- script: `presets/unobserved-remove.json`
- LWW tie bias: `remove`
- description: Replica c issues a remove before it has ever observed a's add. The OR-Set remove is effectively empty, but LWW still records a later remove timestamp that suppresses the earlier add once replicas merge.
- story: The final states diverge on notebook: OR-Set leaves it present because the remove only tombstoned observed tags, while LWW leaves it absent after comparing add=1 and remove=4 under remove-wins ties.
- OR-Set final membership: a=notebook; b=notebook; c=notebook
- LWW final membership: a=∅; b=∅; c=∅
- detail bundle directory: `comparison-presets/unobserved-remove`
- direct artifacts: [bundle](comparison-presets/unobserved-remove/index.html) · [zip](comparison-presets/unobserved-remove/unobserved-remove-bundle.zip) · [comparison](comparison-presets/unobserved-remove/comparison.html) · [timeline](comparison-presets/unobserved-remove/timeline.html) · [replay](comparison-presets/unobserved-remove/replay.html) · [anti-entropy](comparison-presets/unobserved-remove/anti-entropy.html) · [snapshot](comparison-presets/unobserved-remove/orset-snapshot.json)
- companion files: [timeline.md](comparison-presets/unobserved-remove/timeline.md) · [timeline.mmd](comparison-presets/unobserved-remove/timeline.mmd) · [timeline.svg](comparison-presets/unobserved-remove/timeline.svg) · [comparison.md](comparison-presets/unobserved-remove/comparison.md) · [comparison.json](comparison-presets/unobserved-remove/comparison.json) · [anti-entropy.md](comparison-presets/unobserved-remove/anti-entropy.md) · [anti-entropy.json](comparison-presets/unobserved-remove/anti-entropy.json)
- divergence notes:
  - `notebook` — OR-Set=present, LWW=absent; OR-Set keeps only observed-remove tombstones, so active tags a:1 can survive. LWW compares add=1 vs remove=4 with remove-wins ties.

### Observed remove yields the same final answer (`observed-remove-sync`)

- script: `presets/observed-remove-sync.json`
- LWW tie bias: `remove`
- description: Replica b first syncs the add and then removes the element, so both models agree on the final absence. This preset is a useful control case beside the divergence-heavy scenarios.
- story: This script converges to the same final membership in both models; the comparison is still useful for showing that OR-Set tracks tags while LWW relies on timestamp ordering.
- OR-Set final membership: a=∅; b=∅; c=∅
- LWW final membership: a=∅; b=∅; c=∅
- detail bundle directory: `comparison-presets/observed-remove-sync`
- direct artifacts: [bundle](comparison-presets/observed-remove-sync/index.html) · [zip](comparison-presets/observed-remove-sync/observed-remove-sync-bundle.zip) · [comparison](comparison-presets/observed-remove-sync/comparison.html) · [timeline](comparison-presets/observed-remove-sync/timeline.html) · [replay](comparison-presets/observed-remove-sync/replay.html) · [anti-entropy](comparison-presets/observed-remove-sync/anti-entropy.html) · [snapshot](comparison-presets/observed-remove-sync/orset-snapshot.json)
- companion files: [timeline.md](comparison-presets/observed-remove-sync/timeline.md) · [timeline.mmd](comparison-presets/observed-remove-sync/timeline.mmd) · [timeline.svg](comparison-presets/observed-remove-sync/timeline.svg) · [comparison.md](comparison-presets/observed-remove-sync/comparison.md) · [comparison.json](comparison-presets/observed-remove-sync/comparison.json) · [anti-entropy.md](comparison-presets/observed-remove-sync/anti-entropy.md) · [anti-entropy.json](comparison-presets/observed-remove-sync/anti-entropy.json)
- divergence notes: none; both models converge to the same final membership here.

