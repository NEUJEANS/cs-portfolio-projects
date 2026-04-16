# Disk Scheduler LOOK / C-LOOK Review — Pass 2

## Focus
CLI ergonomics and real command execution.

## Findings
1. The original root-level `--requests nargs='*'` parsing made inline request examples brittle because the subcommand token could be swallowed as another request.
2. README examples needed to match a command order that actually works for both `simulate` and `compare`.

## Fixes made
- moved request/input/start/direction options onto the subparsers so inline request lists work with `simulate` and `compare`
- updated the README commands and CLI regression test to use the working subcommand-first syntax
