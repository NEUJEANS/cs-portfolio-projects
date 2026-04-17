# Wrap-up — 2026-04-17 11:58 UTC

## What changed
- added Mini MapReduce benchmark annotation-view controls: `--annotation-severity`, `--annotation-limit`, and `--annotation-overflow`
- rendered annotation-view summaries in Markdown/HTML reports so filtered or collapsed reviewer callouts stay explainable
- expanded the bundled `plugins_average_score.py` project-week notes with secondary `watch` / `info` callouts to exercise filtering and overflow-summary behavior
- added project-level checklist tracking for Mini MapReduce and updated the README with the new annotation-view workflow
- generated committed example artifacts under `docs/artifacts/mini-mapreduce/` for the filtered project-week benchmark report
- kept default benchmark JSON cleaner by omitting `annotation_view` when the view feature is unused

## Tests and reviews run
- `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- `python3 -m py_compile projects/mini-mapreduce-lab/mapreduce.py projects/mini-mapreduce-lab/plugins_average_score.py projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- smoke artifact generation:
  - `python3 projects/mini-mapreduce-lab/mapreduce.py benchmark --job plugin --plugin projects/mini-mapreduce-lab/plugins_average_score.py --scenario skewed --dataset-family project-week --records 240 --shard-size 30 --reducers 2 4 --annotation-severity risk watch --annotation-limit 1 --annotation-overflow summary --output docs/artifacts/mini-mapreduce/2026-04-17-annotation-view-benchmark.json --csv-output docs/artifacts/mini-mapreduce/2026-04-17-annotation-view-benchmark.csv --heatmap-output docs/artifacts/mini-mapreduce/2026-04-17-annotation-view-heatmap.csv --report-output docs/artifacts/mini-mapreduce/2026-04-17-annotation-view-report.md --html-output docs/artifacts/mini-mapreduce/2026-04-17-annotation-view-report.html`
- review pass 1: JSON payload audit; found/fixed the new `annotation_view` metadata leaking into unrelated benchmark outputs with all-zero values
- review pass 2: coverage/doc audit; found/fixed missing README/checklist guidance plus missing CLI regression coverage for the new flags
- review pass 3: artifact audit; generated the committed annotation-view artifacts and rechecked repo-relative plugin paths plus collapsed-callout output
- secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- sync safety: fetched `origin/main` before editing and again immediately before commit/push; branch stayed in sync throughout the slice

## Commit hash
- implementation commit: `9e920b5097c55b0bd8874947b5fc40e84ec8d866`

## Next step
- add batch benchmark presets that emit both full and filtered annotation views in one run for side-by-side portfolio screenshots
