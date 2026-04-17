# Static-site-generator sitemap + RSS review — pass 1

## Focus
Author-facing docs and checklist consistency for the new site-metadata workflow.

## Issue found
- The implementation exposed `_site.json`, `sitemap.xml`, `rss.xml`, and page-level opt-outs, but the broader project checklist and slice artifacts had not been updated yet, which made the slice less resumable and easy to miss.

## Fix applied
- Added the new completed slice entry to `docs/checklists/static-site-generator.md`.
- Added the dedicated resumable slice checklist.
- Refreshed the README/site-metadata explanation so the new workflow is documented alongside the implementation.

## Result
- The code, README, and project-level tracking now describe the same shipped feature set.
