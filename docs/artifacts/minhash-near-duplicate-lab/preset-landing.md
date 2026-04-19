# MinHash preset bundle landing page

A side-by-side landing page for the curated mixed-language, data-science, systems, and web-dev MinHash demo bundles.

- Generated at: `2026-04-19T17:02:53.576026+00:00`
- Presets compared: 4
- Total files across bundles: 27
- Total near-duplicate pairs across bundles: 5

## Preset comparison cards

### Mixed Markdown, code, and notebook MinHash preset

A graph-search study bundle that intentionally duplicates the BFS story across Markdown, Python, and notebook files.

- Preset key: `mixed-markdown-code-notebook`
- Files written: 6
- Pairs detected: 1
- Extensions: .ipynb=1, .md=3, .py=2
- Recommended glob: `*.md,*.py,*.ipynb`
- Token mode: `code` | normalize identifiers: `True` | normalize literals: `True`
- Suggested command: `python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.py,*.ipynb' --token-mode code --shingle-size 4 --num-hashes 64 --bands 8 --threshold 0.2 --normalize-identifiers --normalize-literals --json`
- Bundle links: [summary json](mixed-markdown-code-notebook/bundle/preset-bundle-summary.json), [summary md](mixed-markdown-code-notebook/bundle/preset-bundle-summary.md), [gallery html](mixed-markdown-code-notebook/bundle/preset-gallery.html)
- Top pair: `bfs_queue.py` <> `bfs_variant.py` | exact=1.0000 estimated=1.0000

### Data-science feature pipeline MinHash preset

A feature-engineering portfolio pack with cloned preprocessing logic spread across Python, Markdown, and notebook artifacts.

- Preset key: `data-science-feature-pipeline`
- Files written: 6
- Pairs detected: 1
- Extensions: .ipynb=1, .md=3, .py=2
- Recommended glob: `*.md,*.py,*.ipynb`
- Token mode: `code` | normalize identifiers: `True` | normalize literals: `False`
- Suggested command: `python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.py,*.ipynb' --token-mode code --shingle-size 4 --num-hashes 64 --bands 8 --threshold 0.15 --normalize-identifiers --json`
- Bundle links: [summary json](data-science-feature-pipeline/bundle/preset-bundle-summary.json), [summary md](data-science-feature-pipeline/bundle/preset-bundle-summary.md), [gallery html](data-science-feature-pipeline/bundle/preset-gallery.html)
- Top pair: `feature_pipeline.py` <> `feature_pipeline_variant.py` | exact=1.0000 estimated=1.0000

### Systems reconciliation MinHash preset

A replica-lag and WAL catch-up corpus with code, runbook, and incident-story near-duplicates for systems design demos.

- Preset key: `systems-churn-reconciliation`
- Files written: 7
- Pairs detected: 1
- Extensions: .json=1, .md=4, .py=2
- Recommended glob: `*.md,*.py,*.json`
- Token mode: `code` | normalize identifiers: `True` | normalize literals: `False`
- Suggested command: `python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.py,*.json' --token-mode code --shingle-size 3 --num-hashes 64 --bands 8 --threshold 0.15 --normalize-identifiers --json`
- Bundle links: [summary json](systems-churn-reconciliation/bundle/preset-bundle-summary.json), [summary md](systems-churn-reconciliation/bundle/preset-bundle-summary.md), [gallery html](systems-churn-reconciliation/bundle/preset-gallery.html)
- Top pair: `replica_sync.py` <> `replica_sync_variant.py` | exact=1.0000 estimated=1.0000

### Web-dev component clone MinHash preset

A frontend-heavy portfolio preset that highlights duplicated dashboard cards, hooks, notes, and CSS assets.

- Preset key: `web-dev-component-clones`
- Files written: 8
- Pairs detected: 2
- Extensions: .css=1, .md=3, .ts=2, .tsx=2
- Recommended glob: `*.md,*.tsx,*.ts,*.css`
- Token mode: `code` | normalize identifiers: `True` | normalize literals: `True`
- Suggested command: `python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.tsx,*.ts,*.css' --token-mode code --shingle-size 4 --num-hashes 64 --bands 8 --threshold 0.15 --normalize-identifiers --normalize-literals --json`
- Bundle links: [summary json](web-dev-component-clones/bundle/preset-bundle-summary.json), [summary md](web-dev-component-clones/bundle/preset-bundle-summary.md), [gallery html](web-dev-component-clones/bundle/preset-gallery.html)
- Top pair: `engagement_summary_card.tsx` <> `user_stats_card.tsx` | exact=1.0000 estimated=1.0000

