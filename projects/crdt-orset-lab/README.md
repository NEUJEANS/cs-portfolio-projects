# crdt-orset-lab

## Overview
Build and inspect an **observed-remove set (OR-Set)**, a classic CRDT that lets replicas add/remove set elements independently and later converge through merges without central coordination.

This project focuses on the interview-useful question: **why doesn't a remove always beat an add in distributed systems?** In an OR-Set, a remove only tombstones the add-tags it has actually observed, so a concurrent or later add can still survive after replicas sync.

## Why it is portfolio-worthy
- demonstrates a real eventually consistent data structure instead of a toy set wrapper
- shows replica-local tag generation, tombstones, and merge/convergence rules clearly
- includes a scriptable cluster simulator so scenarios are resumable and easy to demo
- produces JSON snapshots that explain active tags, observed tags, and tombstones per replica
- now exports Markdown, Mermaid, and SVG timeline artifacts so the distributed story is screenshot-friendly instead of buried in raw JSON
- covers a distributed-systems topic that pairs well with the repo's Raft, vector-clock, Chord, and snapshot labs

## Stack
- Python 3
- standard library only

## Features
- OR-Set add operations generate replica-scoped unique tags such as `a:1`
- remove operations tombstone only the tags currently observed on that replica
- merge is associative, commutative, and idempotent for replica state
- cluster simulator supports scripted `add`, `remove`, and `sync` steps across replicas
- sync can run `both`, `forward`, or `reverse` to model anti-entropy or one-way propagation
- JSON snapshots expose converged membership plus per-replica `active_tags`, `observed_tags`, and `tombstones`
- convergence checks require full replica-state equality, not just matching element membership
- optional timeline exports render the same run as Markdown notes, Mermaid sequence diagrams, static SVG portfolio cards, and a small HTML gallery/index page
- optional JSON snapshot export writes the exact machine-readable replica/timeline state that backs the gallery links
- includes a committed sample scenario that demonstrates a remove not deleting a concurrent/new add

## Usage
```bash
python3 crdt_orset_lab.py run-script --replicas a b c --script sample_ops.json
python3 crdt_orset_lab.py add --replicas a b --replica a --element notebook
python3 crdt_orset_lab.py remove --replicas a b c --seed-script sample_ops.json --replica b --element notebook
python3 crdt_orset_lab.py sync --replicas a b c --seed-script sample_ops.json --source a --target b --direction forward
```

### Export timeline artifacts for the sample scenario
```bash
python3 crdt_orset_lab.py run-script \
  --replicas a b c \
  --script sample_ops.json \
  --timeline-markdown-out ../../docs/artifacts/crdt-orset-lab/sample-ops-timeline.md \
  --timeline-mermaid-out ../../docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd \
  --timeline-svg-out ../../docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg \
  --timeline-html-out ../../docs/artifacts/crdt-orset-lab/index.html \
  --json-out ../../docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json
```

Timeline export flags are also available on the single-step `add`, `remove`, and `sync` commands so ad-hoc demos can still emit artifacts. The HTML gallery is meant for browser-friendly navigation, while `--json-out` preserves the exact raw snapshot behind the rendered story.

### Script format
`sample_ops.json` uses this shape, and the CLI also accepts a plain top-level JSON list of operation objects when you do not need wrapper metadata:

```json
{
  "operations": [
    {"op": "add", "replica": "a", "element": "notebook"},
    {"op": "sync", "source": "a", "target": "b", "direction": "both"},
    {"op": "remove", "replica": "b", "element": "notebook"}
  ]
}
```

Supported operations:
- `add` — requires `replica` and `element`
- `remove` — requires `replica` and `element`
- `sync` — requires `source` and `target`, optional `direction` (`both`, `forward`, `reverse`)

## Sample scenario story
The committed `sample_ops.json` walks through this sequence:
1. replica `a` adds `notebook` with tag `a:1`
2. `a` and `b` sync, so `b` now observes `a:1`
3. `b` removes `notebook`, tombstoning only `a:1`
4. replica `c` independently adds `notebook` with tag `c:1`
5. later syncs spread both the tombstone and the new tag
6. all replicas converge on `notebook` still being present because `c:1` was never removed

That makes the OR-Set semantics visible in a way students can explain during a systems interview.

## Committed artifact examples
- `docs/artifacts/crdt-orset-lab/index.html` — browser-friendly gallery/index that links the source scenario script plus the full derived artifact bundle together
- `docs/artifacts/crdt-orset-lab/sample-ops-timeline.md` — step-by-step Markdown table for code review or notes
- `docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd` — Mermaid sequence diagram source for editable replica timelines
- `docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg` — screenshot-ready timeline card for README/slide use
- `docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json` — raw replica/timeline/convergence state for tooling or diffs

## Test
```bash
python3 -m unittest discover -s projects/crdt-orset-lab -p "test_*.py"
```

## Future improvements
- add delta-state payload inspection so merge traffic size can be discussed explicitly
- add another CRDT variant such as an LWW-element-set or PN-counter bundle for side-by-side comparison
- add a comparison page that shows OR-Set vs LWW-element-set behavior on the same scripted scenario
