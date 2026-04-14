# Task Tracker Export Review Pass 1

Date: 2026-04-14

## Focus
Basic correctness after adding the export command.

## Findings
1. `cli.py` had malformed newline string literals from a scripted rewrite, causing import-time `SyntaxError`.
2. Export stdout/file printing paths needed a stable newline branch.

## Fixes applied
- repaired `"\n".join(...)` rendering in table output
- repaired export stdout printing newline handling

## Verification
- reran unit tests after syntax repair
