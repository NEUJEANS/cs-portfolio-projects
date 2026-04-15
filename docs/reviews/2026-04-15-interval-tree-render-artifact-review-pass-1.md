# Interval Tree Render Artifact Review - Pass 1

## Focus
Correctness and CLI behavior for the new trace artifact export flow.

## Findings
1. `--format svg` was accepted even when no `--output` path was provided, which made the flag misleading.
2. Needed a regression test to lock in the expected parser error for that misuse case.

## Fixes made
- added validation in `command_trace()` so non-default `--format` requires `--output`
- added a CLI regression test covering the parser error path

## Result
The trace command now keeps the simple default JSON/DOT behavior while rejecting ambiguous flag combinations.
