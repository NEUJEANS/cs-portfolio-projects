# Review pass 3 — static-site-generator date archives

## What I checked
- generated archive URLs inside sitemap output
- README/checklist consistency with the finished slice
- resumability notes for the next follow-up

## Issue found
- the archive integration test verified the new HTML pages but did not yet assert that generated archive URLs were included in `sitemap.xml`

## Fix applied
- added explicit sitemap assertions for `archives/` and `archives/2026/`
- updated README + checklist copy so archive generation and the `archive: false` opt-out are documented for future runs
