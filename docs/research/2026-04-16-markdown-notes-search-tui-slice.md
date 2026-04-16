# markdown-notes-search TUI slice research

## Why this slice
`markdown-notes-search` already had ranking, section anchors, backlinks, cache reuse, and editor jump commands. The clearest unfinished portfolio gap was interactive browsing: users could find the right note, but scanning several close matches still meant rerunning the CLI or copying paths into an editor.

## Brief references reviewed
- Python curses HOWTO: terminal UIs are best modeled as explicit screen repaint loops with keyboard handling and separate windows/panes.
- Python curses library docs: expect terminal-dependent behavior, handle redraws conservatively, and keep the logic that formats display content testable outside the live curses session.

## Slice decisions
- use standard-library `curses` so the project stays dependency-light and interview-friendly
- keep layout simple: ranked list on the left, preview pane on the right
- keep TUI-specific formatting in pure helper functions so unit tests can validate truncation and preview rendering without needing a real terminal
- preserve existing CLI modes (`plain text`, `--json`, `--open-result`) instead of replacing them
- let `Enter` reuse the existing editor-command path so TUI navigation and editor jump behavior stay consistent

## Risks to watch
- narrow terminals can make list/detail panes unreadable, so the UI should show a resize prompt instead of crashing
- curses code can become hard to test if rendering logic is mixed directly into the event loop
- line wrapping should preserve important metadata like section anchors and backlinks instead of truncating everything into a single long line
