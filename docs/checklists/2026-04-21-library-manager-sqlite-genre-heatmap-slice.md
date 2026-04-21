# Checklist — 2026-04-21 library-manager-sqlite genre heatmap slice

- [x] sync-check `main` against `origin/main` before editing (`ahead/behind 0/0`, no remote drift)
- [x] confirm the next weakest library-manager follow-up is a one-glance genre heatmap on top of the existing trend export
- [x] do brief research on SVG accessibility and color/luminance guidance for readable heatmap output
- [x] capture a short refresh/self-test note for heatmap snapshot design and share calculations
- [x] add a `genre-heatmap` snapshot builder plus CSV and SVG renderers
- [x] expose `genre-heatmap` on the CLI with stdout and artifact-writing modes
- [x] generate committed sample heatmap artifacts under `docs/artifacts/library-manager-sqlite/`
- [x] extend automated coverage for the heatmap snapshot, renderers, and CLI flow
- [x] update the project README and main library-manager checklist so the slice is resumable
- [x] run review pass 1 and fix issues found
- [x] run review pass 2 and fix issues found
- [x] run review pass 3 and fix issues found
- [x] run validation and smoke checks
- [x] run secret scan before push
- [ ] commit feature + wrap-up
- [ ] push safely to `origin/main`
