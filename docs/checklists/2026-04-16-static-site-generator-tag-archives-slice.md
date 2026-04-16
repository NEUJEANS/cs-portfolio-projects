# Static site generator tag archives slice

- Timestamp: 2026-04-16 13:19 UTC
- Project: `static-site-generator`
- Goal: generate portfolio-friendly tag archive pages directly from front matter so visitors can browse related work without a CMS.

## Plan
- [x] verify repo sync state before editing
- [x] inspect current README/checklist/code to confirm the weakest missing slice
- [x] skip extra web research because tag archives are a direct extension of the current metadata and template flow
- [x] skip extra language refresh because the slice stays within the existing Node/path/rendering patterns
- [x] update checklist/docs so the slice is resumable
- [x] add generated `tags/` index and per-tag archive pages
- [x] link page-level tag pills into those generated archive pages and surface a `Tags` nav entry
- [x] expand automated tests for generated archives, deduplicated tags, and nested relative links
- [x] run focused tests and a syntax check
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up
