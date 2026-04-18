# Checklist — CRDT OR-Set replay slice — 2026-04-18

- [x] verify `main` matches `origin/main` before editing and preserve the existing local replay diff
- [x] do brief HTML replay / accessibility research only as needed for the scrubber and live-announcement behavior
- [x] do a short Python / CLI self-test refresh for replay export wiring
- [x] update `projects/crdt-orset-lab/CHECKLIST.md` and add a dedicated replay-slice checklist note
- [x] add a first-class replay / animation HTML export that scrubs replica state alongside the anti-entropy transfer table
- [x] generate and commit replay artifact bundles for `sample_ops.json` and `sample_compare_ops.json`
- [x] update README usage, committed artifact examples, and future follow-up notes
- [x] add regression coverage for replay-frame construction, replay HTML rendering, replay accessibility hooks, and CLI replay export wiring
- [x] run targeted tests, smoke checks, and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and write a wrap-up note
