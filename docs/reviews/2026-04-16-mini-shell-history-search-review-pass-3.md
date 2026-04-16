# Mini Shell History Search Review — Pass 3

## Findings
1. The helper that powers both prefix and substring search had no explicit callable type annotation.
2. The README wording could be read as if substring search inspected command output instead of stored command text.

## Fixes applied
- added a `Callable[[str], bool]` annotation to the shared history-match helper
- clarified the README note so search semantics point at stored command text

## Result
The implementation and docs now describe the same behavior more precisely.
