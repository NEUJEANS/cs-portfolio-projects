# 2026-04-14 pathfinding visualizer review log

## Review pass 1 - code correctness
Findings:
- the original upgrade version silently dropped blank rows while parsing maps, which could hide malformed input

Fixes:
- preserve rows during parsing and reject blank internal rows through rectangular validation

## Review pass 2 - CLI behavior
Findings:
- file-open errors were not converted into a clear CLI error
- no-path runs printed output but still exited successfully, which is weaker for automation

Fixes:
- catch `OSError` and exit with a readable `file error:` message
- return exit code `1` when no path is found after printing the summary/rendered map

## Review pass 3 - docs/tests alignment
Findings:
- tests did not cover the blank-row parser edge case
- README did not mention the non-zero exit behavior for no-path runs

Fixes:
- add a blank-row parser test
- update README feature list to mention script-friendly exit behavior

## Validation after review fixes
- `python3 -m unittest discover -s projects/pathfinding-visualizer -p 'test_*.py'` -> pass (6 tests)
- no-path CLI smoke test -> prints summary/rendered map and exits with code `1`
- malformed blank-row map smoke test -> exits with code `2` and a clear `map error:` message
