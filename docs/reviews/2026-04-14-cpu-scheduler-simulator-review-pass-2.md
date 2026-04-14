# CPU Scheduler Simulator Review — Pass 2

## Focus
Input validation and CLI edge cases.

## Findings
1. Round Robin should explicitly reject non-positive quantum values.
2. Duplicate process ids were already validated correctly.

## Fixes made
- kept explicit `quantum > 0` validation in the simulator
- added a dedicated test covering invalid Round Robin quantum input
