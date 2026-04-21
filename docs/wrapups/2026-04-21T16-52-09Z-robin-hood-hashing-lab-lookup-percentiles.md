# Wrap-up — 2026-04-21T16:52:09Z — robin-hood-hashing-lab lookup percentiles

## What changed
- added `successful_lookup_probe_histogram` to the raw benchmark JSON/CSV outputs so successful lookups preserve enough distribution detail for pooled percentile summaries
- taught the Robin Hood benchmark summarizer to derive pooled successful and unsuccessful lookup `avg / p50 / p95 / max` callouts from histogram data across deterministic trials
- added a new `Lookup percentile callouts` section to the Markdown and HTML benchmark reports plus a compact `Lookup tail winners` table against the linear-probing baseline
- refreshed the committed Robin Hood sample benchmark artifact bundle so the report, dashboard, PNG, CSV, and JSON all reflect the new lookup-tail story
- refreshed the project README, checklist, slice checklist, research note, self-test note, and review log for resumability

## Validation
- `python3 -m py_compile projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py tests/test_robin_hood_hashing_lab.py`
- `python3 -m unittest tests.test_robin_hood_hashing_lab -v` (`22/22`)
- real benchmark artifact regeneration for committed Markdown, HTML, PNG, CSV, and JSON outputs
- deterministic rerun checks comparing repeated Markdown/HTML/PNG/CSV/JSON outputs byte-for-byte via `cmp`
- JSON/CSV smoke checks confirming `successful_lookup_probe_histogram` is emitted in the committed benchmark outputs
- `git diff --check`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (0 verified, 0 unknown)

## Review passes
1. flipped the p95 delta sign so positive tail deltas consistently mean linear probing had the longer tail and Robin Hood won that slice
2. collapsed duplicated lookup-average lines in the HTML detail cards into one compact hit callout and one compact miss callout
3. extracted the optional HTML tail-winner block into `lookup_tail_panel_html` so the page template stays easier to edit safely

## Commit
- feature commit: `2d0c5be` (`feat(robin-hood-hashing-lab): add lookup percentile callouts`)

## Next step
- support string and integer key generators for more workload shapes
