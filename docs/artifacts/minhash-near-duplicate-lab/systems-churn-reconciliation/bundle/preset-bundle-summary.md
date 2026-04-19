# Systems reconciliation MinHash preset

A replica-lag and WAL catch-up corpus with code, runbook, and incident-story near-duplicates for systems design demos.

- Preset key: `systems-churn-reconciliation`
- Files written: 7
- Extensions: .json=1, .md=4, .py=2
- Pairs detected at the recommended threshold: 1
- Recommended glob: `*.md,*.py,*.json`
- Token mode: `code`
- Normalize identifiers: `True`
- Normalize literals: `False`
- Shingle size: `3` | Hashes: `64` | Bands: `8` | Threshold: `0.15`

## Suggested scan command

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.py,*.json' --token-mode code --shingle-size 3 --num-hashes 64 --bands 8 --threshold 0.15 --normalize-identifiers --json
```

## File cards

### `README.md`
- Type: `.md`
- Bytes: `129`
- Preview: # Replica reconciliation notes

### `different_domain.md`
- Type: `.md`
- Bytes: `104`
- Preview: # Different topic

### `incident_timeline.md`
- Type: `.md`
- Bytes: `110`
- Preview: # Incident timeline

### `lag_demo.json`
- Type: `.json`
- Bytes: `206`
- Preview: {

### `replica_sync.py`
- Type: `.py`
- Bytes: `387`
- Preview: def reconciliation_plan(status_rows):

### `replica_sync_variant.py`
- Type: `.py`
- Bytes: `362`
- Preview: def catchup_actions(nodes):

### `runbook.md`
- Type: `.md`
- Bytes: `150`
- Preview: # Replica lag runbook

## Top near-duplicate pairs

- `replica_sync.py` <> `replica_sync_variant.py` | exact=1.0000 estimated=1.0000 shared_bands=8

