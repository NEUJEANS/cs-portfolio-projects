# Mini Shell Persistent History Review — Pass 3

## Findings
1. `load_history()` would preserve blank lines from a hand-edited history file, which could create empty-looking numbered entries in later sessions.
2. There was no regression test covering that small but realistic file-cleanliness edge case.

## Fixes applied
- filtered empty lines when loading the history file
- added a unit test that verifies blank lines are ignored while non-empty command lines are preserved

## Result
The persisted history loader is a little more robust against manual edits and noisy files.
