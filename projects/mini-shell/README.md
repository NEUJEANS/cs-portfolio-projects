# mini-shell

## Overview
A compact Python shell that demonstrates tokenization, built-ins, environment-variable expansion, persistent command history, I/O redirection, and multi-process pipelines.

## Stack
- Python 3
- standard library only (`os`, `shlex`, `subprocess`)

## Features
- in-process built-ins: `cd`, `pwd`, `echo`, `history`, `exit`
- `$NAME` / `${NAME}` environment-variable expansion
- persistent command history loaded at REPL startup and appended across sessions
- numbered `history` output plus full-line `!!` / `!N` replay
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

By default, the REPL keeps history in `~/.mini_shell_history`.
Set `MINI_SHELL_HISTORY_FILE` to override that path, or set it to an empty string to disable persistent history.
(If you call `run_command()` directly in tests or another script, pass a `history_path` argument to enable the same file-backed behavior.)

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
/tmp$ !!
   1  echo hello alice
   2  cat < notes.txt | python3 -c "import sys; print(sys.stdin.read().upper().strip())"
   3  history
/tmp$ history -c
/tmp$ exit
```

Notes:
- builtins can redirect stdout, but builtin stdin redirection is intentionally out of scope for this focused slice
- pipelines support file input on the first stage and file output on the last stage
- history replay is intentionally limited to full-line `!!` and `!N` commands; inline substitutions like `sudo !!` are not implemented yet
- unlike Bash, `history -c` in this project clears both the in-memory list and the configured history file to keep the educational implementation predictable
- history stores the executed expanded command line, so replayed commands show up as the concrete command that ran

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is portfolio-worthy
This project shows several core systems ideas in a small package: command parsing, process spawning, shell-local state, persistent command-history management, Unix-style pipelines, file-descriptor-style redirection, and defensive error handling.

## Future Improvements
- background jobs and job control
- richer history search / prefix replay and configurable history size limits
- richer parser support for stderr redirects, combined operators, and shell quoting edge cases
- shell-local stdin/stdout handling for builtins beyond the current focused slice
