# 2026-04-21 robin-hood-hashing-lab delete-heavy slice

- [x] check branch/remote state, fetch, and confirm local vs remote drift before editing
- [x] do brief research on Robin Hood backward-shift deletion behavior to confirm the post-removal variance story is worth benchmarking
- [x] do a short Python/self-test refresh for the benchmark/report pipeline (`py_compile` + focused unit tests)
- [x] update the Robin Hood hashing checklist so this slice stays resumable
- [x] add delete-heavy benchmark workloads and delete probe metrics to the benchmark pipeline
- [x] extend Markdown/HTML/CSV/JSON benchmark artifacts so delete-heavy runs are visible in committed portfolio outputs
- [x] add or extend regression coverage for delete-heavy workload parsing, deletion metrics, wrapped linear-probing deletes, and CLI exports
- [x] review the slice at least 3 times and fix issues found
- [x] regenerate the committed benchmark artifact bundle
- [x] run targeted tests, smoke checks, determinism checks, and `git diff --check`
- [x] run secret scan before push
- [x] commit, push, and append the wrap-up
- [ ] next: add unsuccessful-lookup benchmark workloads/histograms so misses become part of the interview story
