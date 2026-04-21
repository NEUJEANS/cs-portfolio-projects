# CPU Scheduler Simulator Review — 2026-04-21 Pass 1

## Focus
Context-switch accounting correctness and report ergonomics.

## Findings
1. The new report formatting only showed overhead metadata when the caller explicitly passed `context_switch_cost`, which made library-style reuse of `format_report(result, algorithm)` less trustworthy.

## Fixes made
- taught `format_report` to fall back to `result["context_switch_cost"]` when the caller does not pass the flag through
- added a regression test covering report generation from a precomputed context-switch result
