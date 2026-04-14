# mini-shell

## Overview
A compact Python shell that demonstrates tokenization, built-ins, environment-variable expansion, and multi-process pipelines.

## Stack
- Python 3
- standard library only (`os`, `shlex`, `subprocess`)

## Features
- in-process built-ins: `cd`, `pwd`, `echo`, `exit`
- `$NAME` / `${NAME}` environment-variable expansion
- external command execution with friendly command-not-found errors
- `cmd1 | cmd2 | cmd3` pipelines for external commands
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
/tmp$ python3 -c "print('alpha beta')" | python3 -c "import sys; print(sys.stdin.read().upper().strip())"
ALPHA BETA
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is portfolio-worthy
This project shows several core systems ideas in a small package: command parsing, process spawning, shell-local state, Unix-style pipelines, and defensive error handling.

## Future Improvements
- input/output redirection (`>`, `<`, `>>`)
- background jobs and job control
- command history and tab completion
- richer parser support for escaping and mixed operators
