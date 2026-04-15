# Static Site Generator Review — Pass 1

## Focus
Parsing robustness and deterministic build behavior.

## Findings
1. Front matter parsing only handled the narrow `\n---\n` fence shape.
2. Files with leading whitespace or CRLF line endings could silently skip metadata parsing.

## Fixes applied
- Replaced delimiter slicing with a regex-based front matter match that accepts leading whitespace and CRLF fences.
- Added a regression test covering leading whitespace plus CRLF input.

## Status
Pass complete; parsing is more resilient without adding dependencies.
