# 2026-04-19 Aho-Corasick Stream Context Review Log

## Review pass 1 — implementation correctness
- Issue found: sampled-context extraction tried to slice a `deque` directly, which broke chunked context tests with `TypeError: sequence index must be integer, not 'slice'`.
- Fix applied: materialized the rolling history before slicing so left-context and match-text extraction work in both streaming and memory-backed paths.
- Recheck: project tests passed after the fix.

## Review pass 2 — API consistency and hot-path cost
- Issue found: the CLI rejected negative `--context`, but the direct Python helpers accepted negative `context_chars`; also the rolling history was being re-materialized once per emitted pattern on the same character.
- Fix applied: added shared non-negative context validation to the direct API helpers and `scan_chunks(...)`, and reused a single `history_chars` snapshot per emitting character.
- Recheck: project tests + root tests passed; chunked JSON/text smoke still emitted sampled contexts correctly.

## Review pass 3 — regression coverage after refactor
- Issue found: after moving memory-mode context generation onto the shared scan path, there was no explicit regression test proving inline `--text --context` still printed excerpts.
- Fix applied: added inline-text CLI coverage plus EOF-truncation coverage for sampled contexts so the shared path is exercised in both memory and streaming modes.
- Recheck: compileall, project tests, repo-level tests, and streaming/memory smoke commands all passed.
