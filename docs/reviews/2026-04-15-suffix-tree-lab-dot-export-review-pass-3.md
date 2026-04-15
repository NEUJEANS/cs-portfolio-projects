# 2026-04-15 suffix-tree-lab DOT export review pass 3

## Focus
Docs/test consistency and repo-wide regression confidence.

## Findings
1. The README DOT example had an extra leading space before `digraph`, which made the pasted example slightly inaccurate.
2. The new slice should be checked against the existing repo test set, not just the project-local tests.

## Fixes
- cleaned the README DOT example formatting.
- reran the project-local tests and the existing repo regression suite covering previously promoted labs.
