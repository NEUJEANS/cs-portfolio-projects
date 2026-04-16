# Mini MapReduce plugin docs pages wrap-up

- Timestamp: 2026-04-16T21:22Z
- Project: `mini-mapreduce-lab`
- Implementation commit: `f80d09b6be3dba8c4a0afcdd6ae6ba7cac427059`

## What changed
- Added `catalog-plugins --docs-dir` support that writes dedicated per-plugin Markdown and HTML docs pages.
- Rewired catalog quick-link landing cards to point at those generated docs pages when `--docs-dir` is supplied.
- Added helper coverage and CLI coverage for generated plugin docs pages, catalog backlinks, and publish-safe repo-relative plugin paths.
- Fixed a review-found issue where public Markdown/HTML catalog and diff artifacts were still embedding absolute local filesystem paths; human-facing artifacts now use repo-relative `projects/...` paths instead.

## Tests and reviews run
- `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py`
- `python3 -m unittest tests/test_mini_mapreduce.py`
- `python3 -m py_compile projects/mini-mapreduce-lab/mapreduce.py projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- temp-dir CLI smoke test: `python3 projects/mini-mapreduce-lab/mapreduce.py catalog-plugins --root projects/mini-mapreduce-lab --diff --report-output ... --html-output ... --docs-dir ...`
- review pass 1: page-generation regression audit
- review pass 2: syntax/import safety via `py_compile`
- review pass 3: CLI smoke validation for docs pages and catalog links
- review pass 4: grep-based publish-safety path leak check after switching report/doc paths to repo-relative output
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Next step
- Explore release-to-release comparison pages or richer docs-site navigation once more bundled plugins exist.
