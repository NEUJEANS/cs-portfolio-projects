# Data-science feature pipeline MinHash preset

A feature-engineering portfolio pack with cloned preprocessing logic spread across Python, Markdown, and notebook artifacts.

- Preset key: `data-science-feature-pipeline`
- Files written: 6
- Extensions: .ipynb=1, .md=3, .py=2
- Pairs detected at the recommended threshold: 1
- Recommended glob: `*.md,*.py,*.ipynb`
- Token mode: `code`
- Normalize identifiers: `True`
- Normalize literals: `False`
- Shingle size: `4` | Hashes: `64` | Bands: `8` | Threshold: `0.15`

## Suggested scan command

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.py,*.ipynb' --token-mode code --shingle-size 4 --num-hashes 64 --bands 8 --threshold 0.15 --normalize-identifiers --json
```

## File cards

### `README.md`
- Type: `.md`
- Bytes: `129`
- Preview: # Feature engineering notes

### `experiment_notes.md`
- Type: `.md`
- Bytes: `129`
- Preview: # Experiment notes

### `feature_demo.ipynb`
- Type: `.ipynb`
- Bytes: `1018`
- Preview: # Feature pipeline demo Notebook version of the same preprocessing steps for portfolio screenshots.

### `feature_pipeline.py`
- Type: `.py`
- Bytes: `282`
- Preview: def normalize_rows(rows):

### `feature_pipeline_variant.py`
- Type: `.py`
- Bytes: `329`
- Preview: def build_features(events):

### `outlier_memo.md`
- Type: `.md`
- Bytes: `119`
- Preview: # Different topic

## Top near-duplicate pairs

- `feature_pipeline.py` <> `feature_pipeline_variant.py` | exact=1.0000 estimated=1.0000 shared_bands=8

