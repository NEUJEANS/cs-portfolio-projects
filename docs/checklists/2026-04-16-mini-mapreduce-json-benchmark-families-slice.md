# Mini MapReduce JSON benchmark families slice

Date: 2026-04-16 08:24 UTC
Project: `mini-mapreduce-lab`

## Slice goal
Extend the built-in `json-group-count` job with realistic synthetic benchmark families so the project can demo reducer skew on JSONL event streams, not just wordcount or plugins.

## Checklist
- [x] confirm repo sync before editing
- [x] pick the next unfinished mini-mapreduce slice from the project checklist
- [x] do brief local research on realistic JSON/event benchmark families
- [x] do a short deterministic JSON fixture refresh and self-test
- [x] update checklist/docs so the slice is resumable
- [x] add `json-group-count` benchmark support with dataset families and `--group-field` benchmark wiring
- [x] extend project-level and repo-level tests for programmatic and CLI benchmark coverage
- [x] update README usage, features, and future-improvement notes
- [x] run targeted tests and at least 3 review passes
- [x] run secret scan before push
- [ ] commit, push, and add wrap-up
