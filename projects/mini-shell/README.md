# mini-shell

## Overview
A compact Python shell that demonstrates tokenization, built-ins, environment-variable expansion, searchable persistent command history with configurable size limits, I/O redirection, and multi-process pipelines.

## Stack
- Python 3
- standard library only (`os`, `shlex`, `subprocess`)

## Features
- in-process built-ins: `cd`, `pwd`, `echo`, `history`, `exit`
- `$NAME` / `${NAME}` environment-variable expansion
- persistent command history loaded at REPL startup and appended across sessions
- configurable history retention limits for both in-memory history and the persisted history file
- numbered `history` output plus full-line `!!`, `!N`, `!prefix`, and `!?substring?` replay
- `history -c` to clear the in-memory history and the configured history file for this focused teaching shell
- input redirection with `<` for standalone external commands and pipeline entrypoints
- output redirection with `>` / `>>` for standalone commands and pipeline final output
- `cmd1 | cmd2 | cmd3` pipelines for external commands
- clear validation for unsupported redirection layouts such as middle-stage pipeline redirects or builtin stdin redirects
- external command execution with friendly command-not-found errors
- safer directory validation for `cd`
- focused automated tests for shell behavior

## Usage
Start the REPL:
```bash
python3 mini_shell.py
```

Start the REPL with a bounded history of the last 3 commands:
```bash
MINI_SHELL_HISTORY_LIMIT=3 python3 mini_shell.py
```

By default, the REPL keeps history in `~/.mini_shell_history`.
Set `MINI_SHELL_HISTORY_FILE` to override that path, or set it to an empty string to disable persistent history.
Set `MINI_SHELL_HISTORY_LIMIT` to a non-negative integer to keep only the most recent commands in memory and on disk; set it to `0` to disable history retention without disabling the rest of the shell.
(If you call `run_command()` directly in tests or another script, pass `history_path=` and optionally `history_limit=` to enable the same file-backed and size-limited behavior.)

Example session:
```text
/tmp$ echo hello $USER
hello alice
/tmp$ cat < notes.txt | python3 -c "import sys; print(sys.stdin.read().upper().strip())"
IMPORTANT IDEAS
/tmp$ history
   1  echo hello alice
   2  cat < notes.txt | python3 -c "import sys; print(sys.stdin.read().upper().strip())"
   3  history
/tmp$ !echo
hello alice
/tmp$ !?notes.txt?
IMPORTANT IDEAS
/tmp$ history -c
/tmp$ exit
```

Notes:
- builtins can redirect stdout, but builtin stdin redirection is intentionally out of scope for this focused slice
- pipelines support file input on the first stage and file output on the last stage
- history replay is intentionally limited to full-line `!!`, `!N`, `!prefix`, and `!?substring?` commands; inline substitutions, word designators, and modifiers like `sudo !!` or `!23:$` are not implemented yet
- `!prefix` replays the most recent stored command that starts with that prefix, while `!?substring?` replays the most recent stored command containing the substring
- unlike Bash's separate `HISTSIZE` and `HISTFILESIZE`, this project uses one `MINI_SHELL_HISTORY_LIMIT` for both in-memory and persisted history so the teaching implementation stays predictable
- `MINI_SHELL_HISTORY_LIMIT=0` disables retention while still letting the REPL run normally
- oversized history files are trimmed on REPL startup when a history limit is configured
- unlike Bash, `history -c` in this project clears both the in-memory list and the configured history file to keep the educational implementation predictable
- history stores the executed expanded command line, so replayed commands show up as the concrete command that ran

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is portfolio-worthy
This project shows several core systems ideas in a small package: command parsing, process spawning, shell-local state, persistent command-history management with bounded retention, Unix-style pipelines, file-descriptor-style redirection, and defensive error handling.

## Future Improvements
- background jobs and job control
- richer history expansion beyond the current full-line `!!`, `!N`, `!prefix`, and `!?substring?` support
- richer parser support for stderr redirects, combined operators, and shell quoting edge cases
- shell-local stdin/stdout handling for builtins beyond the current focused slice
