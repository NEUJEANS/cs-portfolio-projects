# Node CLI Refresh — file-organizer-cli — 2026-04-14

## Refreshed concepts
- `fs.promises.rename()` is ideal for same-device moves.
- Cross-device moves need copy-then-delete fallback.
- `node:test` is enough for small portfolio CLIs without extra dependencies.
- CLI quality improves a lot with explicit flags and predictable report formatting.

## Quick self-test
- Could I explain when `rename` fails with `EXDEV`? Yes.
- Could I implement a no-mutation dry run cleanly? Yes.
- Could I preserve files without overwriting existing names? Yes.
- Could I test recursive traversal without looping into bucket folders? Yes.
