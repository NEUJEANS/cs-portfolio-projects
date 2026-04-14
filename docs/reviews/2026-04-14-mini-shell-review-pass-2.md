# Mini Shell Review Pass 2

Focus: parser robustness.

## Findings
- Initial pipeline splitting used a plain string split on `|`, which would incorrectly split commands that contain a literal pipe inside quotes.

## Fixes made
- replaced naive splitting with quote-aware pipeline parsing
- added a regression test proving quoted pipe characters stay inside one command
