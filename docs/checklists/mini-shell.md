# Mini Shell Checklist

Status: vertical slice 4 in progress
Last updated: 2026-04-16

## Vertical slice 2
- [x] identify mini-shell as one of the weakest current projects
- [x] do brief research/design note for stronger shell features
- [x] do short Python subprocess/shlex refresh and self-test
- [x] implement environment variable expansion
- [x] implement `echo` builtin
- [x] implement pipelines between external commands
- [x] improve `cd` validation and command error reporting
- [x] expand automated tests
- [x] run tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## 2026-04-16 redirection slice
- [x] re-check repo sync state before editing
- [x] inspect `mini-shell` and confirm I/O redirection is the next meaningful unfinished shell feature
- [x] skip external web research because the redirection slice is already well-scoped from the existing README/checklist
- [x] do a short `shlex` / `subprocess` / file-handle refresh with a quick self-test
- [x] support input redirection with `<` for standalone external commands and pipeline entrypoints
- [x] support output redirection with `>` / `>>` for standalone commands and pipeline final output
- [x] validate unsupported redirection layouts clearly for pipeline middle stages and builtin stdin
- [x] update README usage, feature list, and future improvements
- [x] expand automated tests for redirect parsing, append mode, builtin output redirect, and pipeline edge redirects
- [x] run focused tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up

## 2026-04-16 history slice
- [x] re-check repo sync state before editing
- [x] inspect `mini-shell` and confirm command history is the next meaningful interactive shell upgrade
- [x] do brief web research against the GNU Bash manual for `history` and `!` expansion conventions
- [x] do a short Python state-management / parse-order refresh with a quick self-test
- [x] add in-memory REPL history state and a `history` builtin
- [x] support full-line `!!` and `!N` replay before parsing
- [x] keep replayed commands predictable by storing expanded executed command lines in history
- [x] update README usage, feature list, and future improvements
- [x] expand automated tests for numbered history output, replay, redirects, and range errors
- [x] run focused tests locally
- [x] perform review pass 1 and fix issues
- [x] perform review pass 2 and fix issues
- [x] perform review pass 3 and fix issues
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
