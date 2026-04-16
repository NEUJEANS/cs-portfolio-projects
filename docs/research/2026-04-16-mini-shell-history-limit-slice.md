# Mini Shell History Size Limit Slice Research

Project: `mini-shell`
Date: 2026-04-16

## Why this slice
The shell already supports in-memory replay and persistent history, but it still keeps history unbounded. A configurable retention cap is the next meaningful shell-quality upgrade because it adds:
- bounded in-memory state for long REPL sessions
- bounded on-disk history growth across sessions
- a realistic configuration surface that mirrors the spirit of Bash history settings

## Brief Bash reference
Brief web research against the GNU Bash manual confirmed the two relevant concepts:
1. `HISTSIZE` limits the in-memory history list
2. `HISTFILESIZE` limits the persisted history file
3. shells typically trim history on startup and/or when saving history back to disk

## Scope choice
Keep this educational slice small and predictable:
1. add one `MINI_SHELL_HISTORY_LIMIT` setting instead of separate memory/file limits
2. apply the same cap to loaded history, newly appended history, and persisted history
3. support `0` to disable retention entirely
4. reject invalid negative or non-numeric limits clearly

## Why one limit instead of two
Bash exposes separate knobs because it is a full shell. This project is a teaching shell, so a single retention limit keeps the behavior easy to explain and test while still demonstrating the core systems idea of bounded state.
