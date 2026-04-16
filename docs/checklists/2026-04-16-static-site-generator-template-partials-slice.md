# Static site generator template partials slice

- Timestamp: 2026-04-16 14:08 UTC
- Project: `static-site-generator`
- Goal: let authors reuse shared header/footer HTML across every generated page without copying boilerplate into each Markdown file.

## Plan
- [x] verify repo sync state before editing
- [x] inspect the existing README/checklist/code to choose the next unfinished slice
- [x] skip extra web research because the slice extends the current local rendering/template flow directly
- [x] skip extra language refresh because the work stays inside the existing Node/CommonJS/test setup
- [x] update checklist/docs so the slice is resumable
- [x] reserve `content/_partials/` for shared `header.html` and `footer.html` templates
- [x] inject page-aware placeholders such as `{{rootPath}}`, `{{navigation}}`, and `{{tags}}` into shared partials
- [x] keep `_partials/` out of page discovery and static-asset copying
- [x] run focused tests, the main `npm test` suite, and a syntax check
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up
