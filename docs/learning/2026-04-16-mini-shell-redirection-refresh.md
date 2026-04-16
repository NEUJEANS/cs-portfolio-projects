# Mini Shell Redirection Refresh and Self-Test

## Refresher notes
- `shlex.shlex(..., punctuation_chars="|<>")` can split shell operators cleanly enough for a small educational shell, including compact forms like `>>out.txt`.
- `contextlib.ExitStack()` is a tidy way to manage optional stdin/stdout file handles without deeply nested `with` blocks.
- `subprocess.run()` is enough for standalone commands with redirected file handles, while `subprocess.Popen()` remains the right choice for multi-process pipelines.
- For a compact shell project, it is better to reject ambiguous pipeline-redirection combinations explicitly than to guess and hide parser mistakes.

## Self-test
1. Why keep using `Popen` for pipelines even after adding redirection?
   - Because each process must stream stdout into the next process's stdin instead of waiting for the first command to finish.
2. What parser upgrade lets the shell recognize `>>out.txt` without requiring spaces?
   - Using `shlex.shlex` with `punctuation_chars="|<>"`.
3. Why reject input redirection on builtins in this slice?
   - Builtins run in-process and this project does not yet emulate shell-level stdin swapping for builtin execution.
