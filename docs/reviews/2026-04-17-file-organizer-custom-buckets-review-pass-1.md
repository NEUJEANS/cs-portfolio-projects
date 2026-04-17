# Review pass 1 — file-organizer custom buckets — 2026-04-17

## Focus
Config safety and recursive traversal behavior.

## Findings
1. **Real bug:** when the config file lives inside the directory being organized, the new implementation can move its own `buckets.json` file into a bucket.

## Fixes made
- added `skipPaths` handling to file collection and automatically skipped the active config path during organize runs
- added a regression test that keeps `buckets.json` in place while still organizing sibling files

## Verification
- `npm test --prefix projects/file-organizer-cli`
