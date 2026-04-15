# 2026-04-15 interval-tree-lab review pass 1

## Focus
Functional code read-through and CLI-path audit.

## Issue found
- `command_demo` and `command_overlap` each computed `find_any_overlap(query)` twice, which was unnecessary and made the CLI handlers a little noisier.

## Fix applied
- stored the overlap result once in a local variable before serializing the JSON payload

## Result
- logic is simpler and avoids duplicate traversal work
