# Mini Shell Redirection Review — Pass 1

## Findings
1. `cd ~` regressed after the parser changes because `cd` still treated `~` like a literal relative directory name.
2. That made the builtin less shell-like even though the new slice otherwise improved path handling.

## Fixes applied
- expanded `~` before resolving the `cd` target path
- added a regression test covering `cd ~`

## Result
The shell keeps the new redirection parser while preserving an expected existing builtin behavior.
