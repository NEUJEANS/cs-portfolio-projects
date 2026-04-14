# Checklist: task-tracker-cli

## Done in earlier slices
- [x] choose first project and define realistic MVP scope
- [x] add research note
- [x] add language/tool refresh note and self-test
- [x] scaffold Python package and CLI entry point
- [x] implement JSON-backed task CRUD flows
- [x] implement task status transitions and summary command
- [x] add README with local run examples
- [x] add pytest coverage for key workflows
- [x] run tests locally
- [x] perform 3 review passes and fix issues found

## 2026-04-14 vertical slice 2 — packaging cleanup + stronger task metadata UX
- [x] identify `task-tracker-cli` as the weakest current project because its packaged entry point still targeted an obsolete implementation
- [x] do brief research if needed (not needed beyond standard Python packaging/CLI compatibility patterns)
- [x] do short Python packaging/import refresh and self-test
- [x] update checklist/docs for a resumable second slice
- [x] consolidate the maintained CLI around `src/task_tracker/`
- [x] keep `task_tracker_cli` as a thin compatibility layer instead of a duplicate implementation
- [x] add a meaningful user-facing improvement (`--clear-due`) while consolidating the package
- [x] refresh README to match the actual runnable feature set
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up

## Next improvements
- [ ] recurring tasks and reminders
- [ ] bulk import from CSV/Markdown checklists
- [ ] richer TUI dashboard
- [ ] SQLite-backed storage option
