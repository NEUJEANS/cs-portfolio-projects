# CPU Scheduler Simulator Review — 2026-04-21 Pass 2

## Focus
README demo clarity and resumability.

## Findings
1. The new overhead slice added a committed sample workload, but the README did not point readers to it directly.
2. The command examples assumed the reader was already inside the project directory.

## Fixes made
- added a dedicated README demo command that uses `artifacts/cpu-scheduler-simulator/context-switch-sample.json`
- clarified that the quick-start commands are meant to be run from `projects/cpu-scheduler-simulator/`
