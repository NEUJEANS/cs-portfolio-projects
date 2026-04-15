# Mini MapReduce plugin benchmark refresh

- Goal: extend the existing benchmark/export pipeline so plugin jobs can be benchmarked without bespoke one-off scripts.
- Decision: reuse the existing `benchmark` command with `--job plugin --plugin ...` instead of adding a second benchmark subcommand.
- Synthetic fixture contract:
  - `wordcount` keeps the existing balanced/skewed text generators.
  - `plugin` uses deterministic `name,score` CSV lines so bundled score plugins can run unchanged.
  - `balanced` rotates evenly across 24 students; `skewed` heavily favors a hot student plus a small warm set.
- Self-test before coding: confirm that plugin benchmark artifacts should carry both a human-readable job name and the plugin path so exported CSV/Markdown/HTML files remain traceable.
- Caveat caught during review: CSV heatmap export must either include the new metadata columns in `fieldnames` or strip extra keys before `DictWriter.writerows`, otherwise it raises on unexpected fields.
