# Checklist — 2026-04-21 library-manager-sqlite genre trend slice

- [x] sync-check `main` against `origin/main` before editing (`ahead/behind 0/0`, no remote drift)
- [x] confirm the next weakest library-manager follow-up is subject-level metadata plus genre analytics
- [x] do brief research on SQLite additive migration and accessible SVG labeling
- [x] capture a short refresh/self-test note for migration-safe metadata and cohort exports
- [x] add migration-safe `genre` metadata on books with stable defaults for older databases
- [x] expose `--genre` on `add` and surface genre metadata in catalog output
- [x] implement `genre-trends` CSV and SVG exports from the circulation history
- [x] generate committed sample artifacts under `docs/artifacts/library-manager-sqlite/`
- [x] extend automated coverage for migration, genre metadata, CLI behavior, and genre trend rendering
- [x] update the project README and main library-manager checklist so the slice is resumable
- [x] run review pass 1 and fix issues found
- [x] run review pass 2 and fix issues found
- [x] run review pass 3 and fix issues found
- [x] run validation and smoke checks
- [ ] run secret scan before push
- [ ] commit feature + wrap-up
- [ ] push safely to `origin/main`
