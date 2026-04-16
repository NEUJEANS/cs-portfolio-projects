# Mini Shell Redirection Slice Research

Project: `mini-shell`
Date: 2026-04-16

## Why this slice
The shell already demonstrates parsing, builtins, environment expansion, and pipelines. The clearest remaining systems-programming gap is classic file redirection:
- `<` for feeding stdin from a file
- `>` for writing stdout to a file
- `>>` for appending stdout to a file

Adding redirection makes the project feel more like a real Unix-style shell without jumping all the way to job control.

## Scope choice
Keep this slice focused and readable:
1. support `<`, `>`, and `>>`
2. allow redirection on standalone commands
3. allow edge redirection for pipelines (`cmd < in | cmd > out`)
4. reject unsupported layouts clearly instead of silently guessing

## Why no extra web research was needed
This behavior is standard shell functionality and the current project already had a clean next-step note pointing at redirection. The main work here is careful parser and file-handle wiring, not API discovery.
