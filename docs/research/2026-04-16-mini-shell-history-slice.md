# Mini Shell History Slice Research

Project: `mini-shell`
Date: 2026-04-16

## Why this slice
After pipelines and redirection, the shell still felt weak as an interactive tool. The next compact but meaningful systems-facing feature is command history:
- a `history` builtin for visibility
- `!!` to replay the most recent command
- `!N` to replay a numbered command from the history list

This improves the shell's day-to-day usability without jumping all the way to job control.

## Brief web research
A quick GNU Bash manual check confirmed two pieces of standard behavior worth mirroring in a focused educational way:
1. the `history` builtin displays numbered entries
2. history expansion uses `!` designators such as `!!` and `!n`

References consulted:
- GNU Bash manual: `Bash History Builtins`
- GNU Bash manual: `History Interaction`

## Scope choice
Keep this slice intentionally small and resumable:
1. maintain in-memory session history inside the REPL
2. add `history` as a builtin
3. support full-line recall forms `!!` and `!N`
4. store the executed expanded command in history so replay stays predictable
5. skip inline substitutions such as `sudo !!`, `!prefix`, and persistent history files for now

## Why this is portfolio-worthy
This adds stateful REPL behavior and command recall semantics on top of parsing and process execution. It makes the project feel more like a real shell while keeping the implementation compact enough for students to explain in interviews.
