# Mini Shell Python Refresh and Self-Test

## Refresher notes
- `shlex.split()` is good for shell-like tokenization without implementing a parser from scratch.
- `os.path.expandvars()` can expand `$NAME` and `${NAME}` patterns in user input.
- `subprocess.Popen()` is more appropriate than `subprocess.run()` when commands need to be chained via pipes.
- built-ins should run in-process because they affect shell state such as the working directory.

## Self-test
1. When should a shell use `Popen` instead of `run`?
   - When stdout from one process must stream into stdin of another process.
2. Why should `cd` be a builtin?
   - A child process cannot change the parent shell's working directory.
3. What helper is enough for basic env-var expansion in this project?
   - `os.path.expandvars()`.
