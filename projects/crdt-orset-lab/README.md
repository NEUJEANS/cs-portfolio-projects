# crdt-orset-lab

## Overview
Build and inspect an **observed-remove set (OR-Set)**, a classic CRDT that lets replicas add/remove set elements independently and later converge through merges without central coordination.

This project focuses on the interview-useful question: **why doesn't a remove always beat an add in distributed systems?** In an OR-Set, a remove only tombstones the add-tags it has actually observed, so a concurrent or later add can still survive after replicas sync.

## Why it is portfolio-worthy
- demonstrates a real eventually consistent data structure instead of a toy set wrapper
- shows replica-local tag generation, tombstones, and merge/convergence rules clearly
- includes a scriptable cluster simulator so scenarios are resumable and easy to demo
- produces JSON snapshots that explain active tags, observed tags, and tombstones per replica
- exports Markdown, Mermaid, SVG, and HTML artifacts so the distributed story is screenshot-friendly instead of buried in raw JSON
- now compares the same scripted history against an **LWW-element-set** so the repo shows not just one CRDT, but why different conflict rules produce different outcomes
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
- every sync event records a digest + delta-style anti-entropy summary so the simulator can explain full-state bytes vs missing-state bytes
- JSON snapshots expose converged membership plus per-replica `active_tags`, `observed_tags`, and `tombstones`
- convergence checks require full replica-state equality, not just matching element membership
- optional timeline exports render the same run as Markdown notes, Mermaid sequence diagrams, static SVG portfolio cards, a small HTML gallery/index page, and a replay/animation page with a scrubber
- optional anti-entropy exports render Markdown/HTML/JSON reports that summarize per-sync transfer sizes, missing tags, tombstones, counters, and bytes saved vs full-state sync
- replay exports keep the replica-state timeline and anti-entropy transfer table on one browser-friendly page for demos, screenshots, and narrated walk-throughs, now with jump-to-sync shortcuts, playback-speed presets, hash-based deep links such as `#step-3` or `#sync-2`, plus built-in copy-link and checkpoint-SVG export actions
- optional `compare-script` runs the same scenario under OR-Set and timestamped LWW-element-set semantics, then emits Markdown/HTML/JSON comparison artifacts that explain where the models diverge
- built-in comparison presets cover both divergence-heavy and control-case scenarios, and `compare-presets` turns them into a single portfolio-friendly summary gallery with optional per-preset detail bundles, portable landing pages, bundled scenario scripts, and downloadable deterministic ZIP packets
- LWW comparison mode supports configurable tie bias (`add` or `remove`) and explicit logical timestamps in the script JSON

## Usage
```bash
python3 crdt_orset_lab.py run-script --replicas a b c --script sample_ops.json
python3 crdt_orset_lab.py add --replicas a b --replica a --element notebook
python3 crdt_orset_lab.py remove --replicas a b c --seed-script sample_ops.json --replica b --element notebook
python3 crdt_orset_lab.py sync --replicas a b c --seed-script sample_ops.json --source a --target b --direction forward
```

### Export timeline artifacts for the sample OR-Set scenario
```bash
python3 crdt_orset_lab.py run-script \
  --replicas a b c \
  --script sample_ops.json \
  --timeline-markdown-out ../../docs/artifacts/crdt-orset-lab/sample-ops-timeline.md \
  --timeline-mermaid-out ../../docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd \
  --timeline-svg-out ../../docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg \
  --timeline-html-out ../../docs/artifacts/crdt-orset-lab/index.html \
  --replay-html-out ../../docs/artifacts/crdt-orset-lab/sample-ops-replay.html \
  --json-out ../../docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json \
  --anti-entropy-markdown-out ../../docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.md \
  --anti-entropy-html-out ../../docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.html \
  --anti-entropy-json-out ../../docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.json
```

Timeline export flags are also available on the single-step `add`, `remove`, and `sync` commands so ad-hoc demos can still emit artifacts. The HTML gallery is meant for browser-friendly navigation, `--replay-html-out` gives you a scrubber/animation page for live walkthroughs (including prev/next sync jumps, adjustable playback speed, URL hashes like `#step-3` / `#sync-2` for deep-linking, one-click copy buttons for the current frame or sync checkpoint, and a standalone SVG download for the current checkpoint), and `--json-out` preserves the exact raw snapshot behind the rendered story. The anti-entropy outputs are useful when you want to explain what a sync had to transfer instead of just showing the final converged state.

### Compare OR-Set vs LWW-element-set on the same scenario
```bash
python3 crdt_orset_lab.py compare-script \
  --replicas a b c \
  --script sample_compare_ops.json \
  --timeline-markdown-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.md \
  --timeline-mermaid-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.mmd \
  --timeline-svg-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.svg \
  --timeline-html-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-timeline.html \
  --replay-html-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-replay.html \
  --json-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-orset-snapshot.json \
  --anti-entropy-markdown-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.md \
  --anti-entropy-html-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.html \
  --anti-entropy-json-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.json \
  --comparison-markdown-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset.md \
  --comparison-html-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset.html \
  --comparison-json-out ../../docs/artifacts/crdt-orset-lab/lww-vs-orset.json
```

`sample_compare_ops.json` is intentionally timestamped so the final OR-Set membership keeps `notebook`, while the LWW-element-set drops it because a later remove timestamp beats the concurrent add. The extra anti-entropy report stays focused on the OR-Set side of that scenario and makes the merge-cost story reviewable alongside the semantics comparison page. The replay page keeps that same OR-Set state trace and the transfer table on one screen so you can narrate the divergence step by step.

### List and summarize the built-in comparison presets
```bash
python3 crdt_orset_lab.py list-presets --json
python3 crdt_orset_lab.py compare-presets \
  --suite-markdown-out ../../docs/artifacts/crdt-orset-lab/comparison-presets.md \
  --suite-html-out ../../docs/artifacts/crdt-orset-lab/comparison-presets.html \
  --suite-json-out ../../docs/artifacts/crdt-orset-lab/comparison-presets.json \
  --detail-output-dir ../../docs/artifacts/crdt-orset-lab/comparison-presets
```

The built-in preset suite currently includes:
- `concurrent-readd` — the same timestamped divergence story as `sample_compare_ops.json`
- `unobserved-remove` — a remove that happens before the remover has seen the original add
- `observed-remove-sync` — a control case where both models converge on the same final absence

This summary command is useful when you want one browser-friendly artifact that demonstrates both **where OR-Set beats naive timestamp ordering** and **where both approaches agree**. When `--detail-output-dir` is present, each preset card also links directly to its own portable bundle landing page, downloadable ZIP packet, comparison page, OR-Set timeline, replay walkthrough, anti-entropy report, bundled scenario script, and raw snapshot bundle.

### Script format
`sample_ops.json` and `sample_compare_ops.json` use this shape, and the CLI also accepts a plain top-level JSON list of operation objects when you do not need wrapper metadata:

```json
{
  "operations": [
    {"op": "add", "replica": "a", "element": "notebook", "time": 1},
    {"op": "sync", "source": "a", "target": "b", "direction": "both"},
    {"op": "remove", "replica": "b", "element": "notebook", "time": 5}
  ]
}
```

Supported operations:
- `add` — requires `replica` and `element`, optional `time` / `timestamp` for LWW comparison mode
- `remove` — requires `replica` and `element`, optional `time` / `timestamp` for LWW comparison mode
- `sync` — requires `source` and `target`, optional `direction` (`both`, `forward`, `reverse`)

## Sample scenario story
The committed `sample_ops.json` walks through this sequence:
1. replica `a` adds `notebook` with tag `a:1`
2. `a` and `b` sync, so `b` now observes `a:1`
3. `b` removes `notebook`, tombstoning only `a:1`
4. replica `c` independently adds `notebook` with tag `c:1`
5. later syncs spread both the tombstone and the new tag
6. all replicas converge on `notebook` still being present because `c:1` was never removed

The committed `sample_compare_ops.json` keeps that same causal shape but assigns explicit timestamps so the LWW-element-set ends up absent while the OR-Set still keeps the concurrent tag. That contrast is exactly the point of the comparison slice.

The built-in preset scripts extend that story with two more resumable cases: `presets/unobserved-remove.json` shows that a replica cannot tombstone tags it has never seen, while `presets/observed-remove-sync.json` acts as a control case where both OR-Set and LWW agree after the remover has observed the add first.

## Committed artifact examples
- `docs/artifacts/crdt-orset-lab/index.html` — browser-friendly OR-Set gallery/index for the baseline sample scenario
- `docs/artifacts/crdt-orset-lab/sample-ops-timeline.md` — step-by-step Markdown table for code review or notes
- `docs/artifacts/crdt-orset-lab/sample-ops-timeline.mmd` — Mermaid sequence diagram source for editable replica timelines
- `docs/artifacts/crdt-orset-lab/sample-ops-timeline.svg` — screenshot-ready timeline card for README/slide use
- `docs/artifacts/crdt-orset-lab/sample-ops-snapshot.json` — raw replica/timeline/convergence state for tooling or diffs
- `docs/artifacts/crdt-orset-lab/sample-ops-replay.html` — replay/animation page that scrubs through replica state and anti-entropy transfer details together, with sync-jump shortcuts, playback-speed presets, deep links for chosen replay/sync checkpoints, copy-link buttons, and checkpoint SVG export
- `docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.html` — browser-friendly digest/delta report for the baseline OR-Set sync sequence
- `docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.md` — Markdown transfer table showing what each sync actually had to ship
- `docs/artifacts/crdt-orset-lab/sample-ops-anti-entropy.json` — machine-readable digest/delta summary for tooling or further analysis
- `docs/artifacts/crdt-orset-lab/lww-vs-orset.html` — side-by-side comparison page explaining why OR-Set and LWW diverge on the timestamped scenario
- `docs/artifacts/crdt-orset-lab/lww-vs-orset-anti-entropy.html` — OR-Set anti-entropy report for the timestamped comparison scenario
- `docs/artifacts/crdt-orset-lab/lww-vs-orset-replay.html` — replay/animation page for the OR-Set side of the timestamped comparison scenario
- `docs/artifacts/crdt-orset-lab/lww-vs-orset.md` — Markdown comparison table for review notes or class writeups
- `docs/artifacts/crdt-orset-lab/lww-vs-orset.json` — full machine-readable OR-Set/LWW comparison snapshot
- `docs/artifacts/crdt-orset-lab/comparison-presets.html` — browser-friendly summary gallery for the built-in divergence/control-case preset suite
- `docs/artifacts/crdt-orset-lab/comparison-presets.md` — Markdown version of the preset suite for notes or code review
- `docs/artifacts/crdt-orset-lab/comparison-presets.json` — machine-readable preset-suite summary for tooling or future batch export steps
- `docs/artifacts/crdt-orset-lab/comparison-presets/concurrent-readd/index.html` — portable landing page for one preset bundle with links to every companion artifact
- `docs/artifacts/crdt-orset-lab/comparison-presets/concurrent-readd/concurrent-readd-bundle.zip` — downloadable packet containing the preset landing page, bundled scenario script, HTML artifacts, Markdown notes, and JSON outputs
- `docs/artifacts/crdt-orset-lab/comparison-presets/concurrent-readd/comparison.html` — per-preset detail page for the divergence case, linked directly from the suite gallery and bundle landing page
- `docs/artifacts/crdt-orset-lab/comparison-presets/concurrent-readd/replay.html` — per-preset OR-Set replay page for the divergence case
- `docs/artifacts/crdt-orset-lab/comparison-presets/observed-remove-sync/index.html` — control-case landing page for the aligned preset bundle
- `docs/artifacts/crdt-orset-lab/comparison-presets/observed-remove-sync/anti-entropy.html` — control-case anti-entropy page that shows a scenario where both models agree on the final membership

## Test
```bash
python3 -m unittest discover -s projects/crdt-orset-lab -p "test_*.py"
```

## Future improvements
- add a cross-preset landing page that can batch-download multiple preset ZIP packets at once
- add more CRDT variants such as PN-counters or MV-registers for broader trade-off comparisons
- add a cross-preset matrix page that groups divergence causes such as unobserved removes, observed removes, and concurrent re-adds
- add PNG/export bundling on top of the replay checkpoint SVG downloads for slide decks that need bitmap assets
