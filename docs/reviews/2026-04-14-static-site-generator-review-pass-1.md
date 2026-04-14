# Static Site Generator Review — Pass 1 (2026-04-14)

## Focus
Metadata parsing and content rendering correctness.

## Findings
1. Front matter parsing only handled LF newlines, which could break files created on Windows.
2. The initial rendering path was too permissive about inline links and did not guard against unsafe URL schemes.

## Fixes applied
- normalized CRLF to LF before front matter parsing
- added `sanitizeHref()` and covered the fallback behavior with tests

## Validation
- `npm test`
