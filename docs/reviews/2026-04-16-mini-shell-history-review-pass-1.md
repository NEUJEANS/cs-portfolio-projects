# Mini Shell History Review — Pass 1

## Findings
1. The new `history` builtin records the executed command line, including redirection syntax, but the new redirect test was still expecting a simplified `history` entry.
2. The README did not yet explain that the shell stores expanded executed command lines instead of the literal recall token.

## Fixes applied
- updated the redirected-history test expectation to match the actual recorded command line
- documented that the shell stores the concrete executed command in history so replay stays predictable

## Result
The implementation, tests, and docs now agree on what the history list represents.
