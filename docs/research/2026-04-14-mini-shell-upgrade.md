# Mini Shell Upgrade Research

Goal: strengthen the existing mini-shell so it demonstrates more systems-programming depth than simple command dispatch.

## Useful portfolio-facing shell features
- tokenization with `shlex` to respect quoted strings
- environment-variable expansion so commands can use `$HOME`-style values
- built-ins for shell-local behavior such as `cd`, `pwd`, and `echo`
- pipelines to demonstrate process composition
- clearer command-not-found and directory-validation errors

## Chosen vertical slice
For this run, add:
1. variable expansion on command tokens
2. `echo` builtin
3. `cmd1 | cmd2 | cmd3` pipelines for external commands
4. stronger `cd` validation and friendly command errors

This keeps the project small enough to remain readable while making it much more convincing as a CS student systems project.
