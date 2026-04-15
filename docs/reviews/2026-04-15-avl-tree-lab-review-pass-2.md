# Review pass 2 - avl-tree-lab

## Focus
- deletion-path clarity and CLI ergonomics

## Findings
1. Trace output for two-child deletion did not explain the successor replacement step, which made interview walkthroughs harder.
2. CLI failures surfaced as Python exceptions instead of consistent machine-readable output.

## Fixes applied
- logged `replace <key> with successor <key>` during two-child deletion
- wrapped CLI command execution in error handling that emits JSON errors and exits with code 2 for invalid operations
- added a CLI test that verifies JSON-formatted error output

## Verification
- reran unit tests and checked the delete trace includes a successor message
