# Mini Shell History Limit Review — Pass 1

## Findings
1. The README explained the new `MINI_SHELL_HISTORY_LIMIT` setting, but it did not show a concrete invocation example.
2. Without a visible example, the new cap felt more abstract than the rest of the shell's usage section.

## Fixes applied
- added a focused README example showing `MINI_SHELL_HISTORY_LIMIT=3 python3 mini_shell.py`

## Result
The usage docs now show the bounded-history feature in the same concrete style as the rest of the project.
