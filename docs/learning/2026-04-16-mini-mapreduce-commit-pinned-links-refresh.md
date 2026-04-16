# Mini MapReduce refresh — commit-pinned GitHub links

Date: 2026-04-16 06:31 UTC
Project: `mini-mapreduce-lab`

## Refreshed idea
- Branch-aware GitHub blob links are great for current browsing, but archival artifacts should also carry a commit SHA so source references keep pointing at the exact inspected code even after later pushes.

## Quick self-test
- `git rev-parse --abbrev-ref HEAD` gives the moving branch ref for reviewer-friendly links.
- `git rev-parse HEAD` gives the immutable commit SHA for archival links.
- A good inspection artifact can include both forms without breaking non-GitHub repos by degrading to `None` when repo metadata is unavailable.
