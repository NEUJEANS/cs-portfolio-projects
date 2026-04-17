# Static-site-generator archive feature cards slice

- [x] identify `static-site-generator` as still unfinished because the archive pages still use plain lists without highlighted entry cards
- [x] skip extra web research because the next slice is already explicitly scoped in the local README/checklist and fits the current archive pipeline directly
- [x] skip extra language refresh because the slice stays inside the existing Node/CommonJS renderer and test harness
- [x] add a resumable checklist for the slice
- [x] generate richer archive layouts with a featured latest entry card plus excerpt cards for remaining dated entries
- [x] derive archive card excerpts from front matter/body content without breaking existing archive navigation
- [x] expand automated tests for featured archive cards, excerpt fallbacks, generated archive pages, and the synced duplicate test entrypoint
- [x] update README and project checklists with the richer archive-card workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan before push
- [ ] commit and push
- [ ] append wrap-up

## Review fixes captured
1. Prevented the newest year-level featured entry from leaving an empty month section when that month only has a single post.
2. Corrected the mirrored regression assertions so the year-page link expectation matches the real relative archive path.
3. Reset the in-progress checklist state so post-push steps stay resumable instead of being marked done too early.
