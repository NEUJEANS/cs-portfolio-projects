# Mini MapReduce commit-pinned inspection links slice

Date: 2026-04-16 06:31 UTC
Project: `mini-mapreduce-lab`

## Slice goal
Make plugin inspection artifacts archival-friendly by surfacing the repo commit SHA and commit-pinned GitHub blob links alongside the existing branch-aware links.

## Checklist
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] skip external web research because the remaining follow-up was already explicitly scoped in the local README/checklist
- [x] do a short git `rev-parse HEAD` / archival-link refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] extend `inspect-plugin` JSON/CSV/Markdown/HTML artifacts with repository commit SHAs and commit-pinned GitHub source URLs
- [x] extend project-level and repo-level tests for commit-pinned inspection metadata and rendered report links
- [x] run tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
