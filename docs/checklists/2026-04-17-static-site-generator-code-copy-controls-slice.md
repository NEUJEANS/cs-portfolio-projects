# 2026-04-17 static-site-generator code copy controls slice

- [x] confirm repo sync before editing
- [x] identify `static-site-generator` as the next worthwhile slice because code samples were polished but still not interactive
- [x] do brief web research on Clipboard API constraints and polite ARIA live-region feedback
- [x] skip extra language refresh because the slice stays inside the current Node/CommonJS renderer plus a small inline browser helper
- [x] update/add checklist docs so the slice is resumable
- [x] add copy-to-clipboard controls and polite status messaging to rendered fenced code blocks
- [x] add a legacy copy fallback for browsers/contexts where `navigator.clipboard.writeText()` is unavailable
- [x] inject the copy helper only on pages that actually include rendered code blocks
- [x] expand automated tests for copy-button markup, helper script generation, and generated-page injection behavior
- [x] keep the duplicate `test_static_site_generator.js` entrypoint synced
- [x] update README with the interactive code-sample workflow and next follow-up
- [x] run tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit, push, and append wrap-up
