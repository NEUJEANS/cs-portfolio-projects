# Mini MapReduce commit-pinned links review — pass 1

Date: 2026-04-16 06:40 UTC
Project: `mini-mapreduce-lab`

## Focus
- repo metadata helper behavior
- branch-aware vs commit-pinned URL separation
- backward-compatible inspection payload shape

## Findings
- `inspect-plugin` now records `plugin_repo_commit` once per inspected plugin and reuses it to build immutable blob URLs.
- Branch-aware URLs still point at `blob/main/...`, while the new commit-pinned URLs point at `blob/<sha>/...`, so reviewers get both current and archival references.
- The helper still degrades safely to `None` outside GitHub-backed repos or when source metadata cannot be derived.

## Result
- No code changes required after this pass.
