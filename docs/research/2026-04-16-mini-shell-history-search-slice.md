# Mini Shell History Search Slice Research

Project: `mini-shell`
Date: 2026-04-16

## Why this slice
The shell already supports numbered replay, persistent history, and bounded retention, but it still lacks the fastest way to recall commands by memory. Adding lightweight search-based replay improves the teaching value because it demonstrates:
- command-history lookup strategies on top of existing stored state
- small user-facing syntax design decisions inspired by real shells
- careful scoping so the project stays understandable instead of growing into a full Bash clone

## Brief Bash reference
Brief web research against GNU Bash's history expansion docs confirmed these event-designator patterns:
1. `!string` refers to the most recent command starting with `string`
2. `!?string?` refers to the most recent command containing `string`
3. Bash supports many more features such as word designators and modifiers, but those are beyond the scope of this teaching shell

Reference used: GNU Bash history/event-designator docs via the GNU manual mirror at MIT.

## Scope choice
Keep this slice intentionally narrow and predictable:
1. support full-line `!prefix` replay for the most recent command whose stored text starts with the prefix
2. support full-line `!?substring?` replay, plus the optional trailing `?` form from the Bash docs
3. keep replay behavior aligned with the existing project rule that history stores the concrete expanded command line that actually ran
4. explicitly leave out inline expansions, `!-N`, word designators, and history modifiers

## Why this scope fits the project
This project is a compact portfolio shell, not a full POSIX shell. Prefix and substring search replay add a real interactive quality upgrade without forcing a much larger parser or surprising behavior surface.
