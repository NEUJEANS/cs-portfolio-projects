# markdown-notes-search TUI refresh

- reviewed the Python `curses` pattern of a small input/render loop wrapped by `curses.wrapper(...)`
- refreshed `textwrap.wrap(...)` usage for keeping preview metadata readable in narrow panes
- self-check reminder: keep terminal-formatting helpers pure so they can be unit tested without needing a live TTY
- practical takeaway: for small portfolio CLIs, a dependency-free list/detail browser is enough to demonstrate product thinking without pulling in a full TUI framework
