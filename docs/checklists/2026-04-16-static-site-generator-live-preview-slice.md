# Static site generator live preview slice

- Timestamp: 2026-04-16 16:09 UTC
- Project: `static-site-generator`
- Goal: let authors preview the generated `dist/` site locally and auto-refresh the browser when watch-mode rebuilds finish.

## Plan
- [x] verify repo sync state before editing
- [x] inspect the current project checklist, README, and working tree to confirm the next unfinished slice
- [x] skip extra web research because the slice is a direct extension of the current watch/build pipeline
- [x] skip extra language refresh because the work stays within the existing Node/CommonJS/http standard-library stack
- [x] update checklist/docs so the slice is resumable
- [x] add CLI support for `--serve` and configurable preview ports
- [x] implement a built-in preview server for the generated output directory with extensionless page routing
- [x] inject browser auto-refresh only when preview mode is paired with watch mode
- [x] cover live preview behavior with focused tests plus the main suite
- [x] run focused tests, the main `npm test` suite, and a syntax check
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up
