# File Organizer CLI Upgrade Research — 2026-04-14

## Goal
Strengthen `file-organizer-cli` so it looks like a thoughtful portfolio project instead of a toy script.

## Brief findings
- `fs.rename()` is fast and atomic on the same filesystem, but can fail with `EXDEV` across devices.
- A safer file organizer should avoid overwriting existing files by generating unique destination names.
- A dry-run mode is a high-value CLI feature because it lets users preview bulk file changes safely.
- Recursive traversal should avoid reprocessing bucket directories that the tool itself creates.

## Sources checked
- Stack Overflow discussions on Node.js `EXDEV` rename behavior and copy/unlink fallback
- General Node.js CLI/file-system best-practice writeups surfaced via web search

## Decisions for this slice
1. Add `--dry-run` support.
2. Add collision-safe destination naming.
3. Add `EXDEV` fallback in the move helper.
4. Add `--recursive` support while skipping known bucket folders.
5. Improve output with a useful summary for README screenshots and demos.
