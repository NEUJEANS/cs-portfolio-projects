# mini-shell

## Overview
A compact Python shell that demonstrates tokenization, built-ins, environment-variable expansion, I/O redirection, and multi-process pipelines.

## Stack
- Python 3
- standard library only (`os`, `shlex`, `subprocess`)

## Features
- in-process built-ins: `cd`, `pwd`, `echo`, `exit`
- `$NAME` / `${NAME}` environment-variable expansion
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

Example session:
```text
/tmp$ pwd
/tmp
/tmp$ echo hello $USER
hello alice
/tmp$ cat < notes.txt | python3 -c "import sys; print(sys.stdin.read().upper().strip())"
IMPORTANT IDEAS
/tmp$ python3 -c "import sys; print(sys.stdin.read().strip().replace(' ', '-'))" < notes.txt > summary.txt
/tmp$ pwd > cwd.txt
/tmp$ echo done>>build.log
```

Notes:
- builtins can redirect stdout, but builtin stdin redirection is intentionally out of scope for this focused slice
- pipelines support file input on the first stage and file output on the last stage

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is portfolio-worthy
This project shows several core systems ideas in a small package: command parsing, process spawning, shell-local state, Unix-style pipelines, file-descriptor-style redirection, and defensive error handling.

## Future Improvements
- background jobs and job control
- command history and tab completion
- richer parser support for stderr redirects, combined operators, and shell quoting edge cases
- shell-local stdin/stdout handling for builtins beyond the current focused slice
