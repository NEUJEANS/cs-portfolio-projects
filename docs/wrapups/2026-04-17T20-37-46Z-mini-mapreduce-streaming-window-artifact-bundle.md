# Mini MapReduce streaming-window artifact bundle slice

- **Timestamp:** 2026-04-17T20:37:46Z
- **Feature commit:** `fc88f42` (`docs(mini-mapreduce): publish streaming window artifact bundle`)
- **What changed:**
  - committed the missing Mini MapReduce streaming-window artifact bundle under `docs/artifacts/mini-mapreduce/`, including the new IoT burst benchmark JSON/CSV/heatmap/Markdown/HTML outputs plus the dedicated `plugin-streaming-window` Markdown/HTML docs page
  - regenerated the shared plugin catalog, comparison diff bundle, and docs index so the committed artifact surface now includes the streaming-window plugin and benchmark links end to end
  - fixed README drift by updating the batched `inspect-plugin` examples to include the newest streaming-window plugin and refreshed the resumable checklist with more concrete next-slice candidates
  - fixed docs-index slug humanization so `iot` labels render as `IoT` instead of `Iot`, and added a repo-level regression test for that acronym-preserving title path
- **Tests / reviews run:**
  - `python3 -m py_compile projects/mini-mapreduce-lab/mapreduce.py projects/mini-mapreduce-lab/plugins_streaming_window.py`
  - `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py` (`106` tests passed)
  - artifact smoke/regeneration: `catalog-plugins --diff --docs-dir ...`, `benchmark --job plugin --plugin projects/mini-mapreduce-lab/plugins_streaming_window.py --scenario skewed --dataset-family iot-burst ...`, and `docs-index`
  - review pass 1: audited the committed docs bundle and found the stale docs index was missing the new streaming-window plugin page/report links; fixed by regenerating the artifact bundle and index
  - review pass 2: checked README/checklist resumability and fixed the batched inspection examples plus next-slice wording drift
  - review pass 3: ran a link/title audit on the regenerated docs index, found `Iot` title casing in generated labels, fixed `humanize_docs_slug()` to preserve `IoT`, then reran tests and artifact generation
  - secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (`0` verified / `0` unknown)
- **Next step:** add the next richer Mini MapReduce plugin example, ideally a rolling-window joins plugin or watermark-aware late-event summary path.
