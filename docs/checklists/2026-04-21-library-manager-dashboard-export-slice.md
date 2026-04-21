# Checklist — 2026-04-21 library-manager-sqlite dashboard export slice

- [x] sync-check `main` against `origin/main` before editing (`ahead/behind 0/0`, no remote drift)
- [x] confirm the next unfinished library-manager follow-up is the recruiter-friendly dashboard export
- [x] do brief dashboard/accessibility research for captions, grouped table sections, and machine-readable timestamps
- [x] capture a short Python/static-export refresh note and self-test
- [x] implement `dashboard` snapshot/export support in the CLI
- [x] render both Markdown and HTML dashboard outputs from the same snapshot data
- [x] make historical snapshots respect the selected reference date instead of leaking future returns/checkouts into past views
- [x] support deterministic `--generated-at` timestamps so committed sample artifacts are reproducible
- [x] extend automated tests for dashboard rendering, CLI export, and reference-date semantics
- [x] generate committed sample artifacts under `docs/artifacts/library-manager-sqlite/`
- [x] update the project README and main project checklist so the slice is resumable
- [x] run review pass 1 and fix issues found
- [x] run review pass 2 and fix issues found
- [x] run review pass 3 and fix issues found
- [x] run validation / smoke / secret scan
- [ ] commit feature + wrap-up
- [ ] push safely to `origin/main`
