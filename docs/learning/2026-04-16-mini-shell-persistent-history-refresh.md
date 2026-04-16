# Mini Shell Persistent History Refresh and Self-Test

## Refresher notes
- Persistent shell history is shared session state, so the cleanest shape for this project is to keep the existing in-memory list and mirror each executed command into a plain UTF-8 line-based history file.
- Loading history once at REPL startup keeps the command runner simple: `run_command()` can stay focused on one command at a time while the REPL owns long-lived session state.
- A configurable history-file path is useful both for users and for tests, because it avoids coupling the project to the real home directory.
- If `history -c` is part of the teaching slice, truncating the file after recording the command is acceptable because the project intentionally treats clear-history as “wipe everything now,” not Bash-perfect compatibility.

## Self-test
1. Why should the REPL load the history file instead of reloading it before every command?
   - Because the REPL owns session state and repeated reloads would complicate replay order and duplicate handling.
2. Why make the history file path configurable?
   - So tests can isolate state in temporary directories and users can override or disable persistence safely.
3. Why is a plain line-based file enough here?
   - Because this shell only records single-line executed commands and does not yet need timestamps, metadata, or advanced merge behavior.
