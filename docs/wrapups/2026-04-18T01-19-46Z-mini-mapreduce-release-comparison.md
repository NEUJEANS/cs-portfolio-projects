# Mini MapReduce release comparison slice

- **Timestamp:** 2026-04-18T01:19:46Z
- **Feature commit:** `e56d3cd` (`feat(mini-mapreduce): add plugin release comparison bundle`)
- **What changed:**
  - added a `compare-plugin-releases` flow to `mapreduce.py` so saved plugin inspection/catalog snapshots can be compared as machine-readable JSON plus publishable Markdown/HTML release summaries
  - extended both project-level and repo-level tests to cover snapshot loading, CLI release-comparison output, docs-index discovery, and normalization of absolute historical plugin paths
  - published a committed Mini MapReduce historical snapshot (`2026-04-17-plugin-catalog.json`), a clean `2026-04-17-vs-current-release-comparison` bundle, and refreshed docs-index artifacts so release comparisons are discoverable next to catalogs/diffs/reports
  - fixed three review-found issues before release: bogus changed-plugin rows from absolute-vs-relative snapshot paths, an over-narrow comparator refactor caught by the new regression test, and a lingering absolute-path leak inside the historical snapshot diff payload
- **Tests / reviews run:**
  - Python refresh/self-test: dataclass field loading + JSON snapshot round-trip
  - `python3 -m py_compile projects/mini-mapreduce-lab/mapreduce.py projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
  - `python3 -m unittest projects.mini-mapreduce-lab.test_mapreduce tests.test_mini_mapreduce` (`120` tests passed)
  - review pass 1: artifact inspection found stale docs-index output and fake changed-plugin rows caused by absolute-vs-relative historical plugin paths; normalized release-comparison diffing and regenerated the bundle
  - review pass 2: the new regression test caught an over-aggressive comparator refactor that dropped full-field comparisons; restored full inspection diffing while normalizing only the plugin path field
  - review pass 3: leak/link audit over the historical snapshot, release-comparison bundle, docs index, and README removed the nested historical absolute-path leak and verified the final summary (`5` added / `0` removed / `0` changed / `2` unchanged)
  - secret scan before push: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (`0` verified / `0` unknown)
- **Next step:** either add docs-site navigation/cross-project landing pages if the artifact surface keeps growing, or move to the next weakest portfolio project outside Mini MapReduce now that the release-comparison/documentation story is publishable.
