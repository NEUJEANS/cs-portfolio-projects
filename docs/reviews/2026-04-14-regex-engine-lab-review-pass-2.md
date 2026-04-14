# Regex engine lab review pass 2

## Focus
Documentation and CLI behavior audit.

## Checks run
- read project README against actual CLI subcommands
- verified sample commands for `fullmatch`, `search`, and `explain`
- checked whether search semantics were documented clearly enough for portfolio readers

## Findings
- README showed the search command but did not explain the engine's leftmost/longest search behavior.

## Fixes applied
- added a short README note clarifying that `search` returns the leftmost match and prefers the longest match for that start position

## Result
Docs now match the implemented behavior more closely.
