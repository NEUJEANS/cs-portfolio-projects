# CPU Scheduler Simulator Review — 2026-04-21 Comparison Pass 3

## Focus
Preset execution coverage and resumability of the new CLI surfaces.

## Findings
1. The compare-path tests covered preset loading well, but normal single-algorithm execution with `--preset` was still only manually implied rather than explicitly guarded.

## Fixes made
- added a CLI regression test that runs a normal Round Robin simulation directly from the committed `interactive-bursts` preset
- reran the full scheduler test suite after the new coverage landed
