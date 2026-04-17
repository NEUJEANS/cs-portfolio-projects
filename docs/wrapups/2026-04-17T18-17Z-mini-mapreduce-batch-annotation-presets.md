# Wrap-up — 2026-04-17 18:17 UTC

## What changed
- added batch benchmark preset support to Mini MapReduce so one benchmark run can emit multiple annotation-view variants without re-running timing measurements
- introduced built-in `full` and `portfolio-tight` annotation presets plus a manifest that points at the shared CSV/heatmap files and each preset’s JSON/Markdown/HTML artifacts
- kept the committed batch manifest portable by using self-relative paths instead of machine-specific absolute directories
- expanded project-level and repo-level tests to cover preset batch generation, manifest output, and CLI regression behavior
- generated committed project-week example artifacts under `docs/artifacts/mini-mapreduce/` for side-by-side full vs portfolio-tight reviewer narratives
- updated the README, project checklist, slice checklist, and learning notes so the slice stays resumable

## Tests and reviews run
- `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- `python3 -m py_compile projects/mini-mapreduce-lab/mapreduce.py projects/mini-mapreduce-lab/plugins_average_score.py projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- smoke artifact generation:
  - `python3 projects/mini-mapreduce-lab/mapreduce.py benchmark --job plugin --plugin projects/mini-mapreduce-lab/plugins_average_score.py --scenario skewed --dataset-family project-week --records 240 --shard-size 30 --reducers 2 4 --annotation-batch-dir docs/artifacts/mini-mapreduce --annotation-batch-prefix 2026-04-17-annotation-batch`
- artifact parity check:
  ```bash
  python3 - <<'PY'
  import json
  from pathlib import Path
  base = Path('docs/artifacts/mini-mapreduce')
  full = json.loads((base/'2026-04-17-annotation-batch-full.json').read_text())
  tight = json.loads((base/'2026-04-17-annotation-batch-portfolio-tight.json').read_text())
  assert full['timings_ms'] == tight['timings_ms']
  assert full['heatmap_rows'] == tight['heatmap_rows']
  assert 'annotation_view' not in full
  assert tight['annotation_view']['hidden_by_limit'] == 1
  print('batch-artifact-check: ok')
  PY
  ```
- review pass 1: manifest portability audit; found/fixed the batch manifest recording an absolute output directory and changed it to self-relative `.`
- review pass 2: regression coverage audit; added assertions in both project-level and repo-level tests so the portable manifest contract stays locked in
- review pass 3: artifact audit; regenerated the committed batch artifacts and rechecked that shared CSV/heatmap metrics stay identical across both preset views
- secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- sync safety: fetched `origin/main` before editing and again immediately before commit; branch stayed in sync throughout the slice

## Commit hash
- implementation commit: `c3b59c0ec7e669488bf2fb616f99cf1630e8113e`

## Next step
- add a lightweight landing page that links plugin catalogs, plugin doc pages, benchmark reports, and annotation-batch manifests into one portfolio-friendly docs index
