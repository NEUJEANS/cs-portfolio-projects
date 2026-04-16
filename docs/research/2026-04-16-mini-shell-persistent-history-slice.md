# Mini Shell Persistent History Slice Research

Project: `mini-shell`
Date: 2026-04-16

## Why this slice
After adding in-memory history replay, the shell still forgot everything between runs. The next meaningful upgrade is to persist command history across REPL sessions so the shell feels more realistic without jumping into job control or a much richer parser.

## Brief web research
A quick GNU Bash manual check highlighted two conventions worth mirroring in a focused way:
1. `HISTFILE` points at the on-disk history file and lets a shell carry history across sessions.
2. `history -c` clears the current history list, even though Bash treats file clearing as a separate concern.

References consulted:
- GNU Bash manual: `Bash Variables` (`HISTFILE`)
- GNU Bash manual: `Bash History Builtins` (`history`, `history -c`)

## Scope choice
Keep this slice intentionally compact and resumable:
1. load prior commands from a configurable history file when the REPL starts
2. append each executed command line to that file as the session runs
3. support `MINI_SHELL_HISTORY_FILE` so tests and users can override or disable persistence cleanly
4. add `history -c` to clear both in-memory and persisted history for this teaching shell
5. skip Bash-level features such as `history -a/-n/-r/-w`, timestamps, deduplication rules, and size limits for now

## Intentional simplification
Real Bash separates clearing the in-memory history list from editing the on-disk history file. For this portfolio project, clearing both at once keeps the behavior easier to explain and test.

## Why this is portfolio-worthy
This slice adds durable REPL state, simple file-backed session recovery, and explicit design trade-offs around compatibility versus teaching clarity. It makes the shell more realistic while staying small enough for interview discussion.
