# Review pass 3 — task-tracker restore slice

- ran a manual CLI smoke flow: add → done → archive → restore `--status todo` → list `--json`
- verified the replay stays resumable: archived snapshots remain immutable, restored tasks are appended, and recurrence metadata survives replay
- audited the README + checklist so the new workflow is documented for future runs
