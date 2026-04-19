# Mixed Markdown, code, and notebook MinHash preset

A graph-search study bundle that intentionally duplicates the BFS story across Markdown, Python, and notebook files.

- Preset key: `mixed-markdown-code-notebook`
- Files written: 6
- Extensions: .ipynb=1, .md=3, .py=2
- Pairs detected at the recommended threshold: 1
- Recommended glob: `*.md,*.py,*.ipynb`
- Token mode: `code`
- Normalize identifiers: `True`
- Normalize literals: `True`
- Shingle size: `4` | Hashes: `64` | Bands: `8` | Threshold: `0.2`

## Suggested scan command

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.py,*.ipynb' --token-mode code --shingle-size 4 --num-hashes 64 --bands 8 --threshold 0.2 --normalize-identifiers --normalize-literals --json
```

## File cards

### `README.md`
- Type: `.md`
- Bytes: `96`
- Preview: # Graph search notes

### `bfs_demo.ipynb`
- Type: `.ipynb`
- Bytes: `1154`
- Preview: # BFS notebook demo Breadth-first search expands the frontier level by level with a queue.

### `bfs_queue.py`
- Type: `.py`
- Bytes: `405`
- Preview: from collections import deque

### `bfs_variant.py`
- Type: `.py`
- Bytes: `417`
- Preview: from collections import deque

### `distant_topic.md`
- Type: `.md`
- Bytes: `116`
- Preview: # Different topic

### `portfolio_reflection.md`
- Type: `.md`
- Bytes: `138`
- Preview: # BFS study guide

## Top near-duplicate pairs

- `bfs_queue.py` <> `bfs_variant.py` | exact=1.0000 estimated=1.0000 shared_bands=8

