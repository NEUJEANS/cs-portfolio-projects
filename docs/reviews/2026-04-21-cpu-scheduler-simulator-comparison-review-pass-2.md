# CPU Scheduler Simulator Review — 2026-04-21 Comparison Pass 2

## Focus
Preset UX consistency and whether the generated dashboard metadata made the workload source obvious.

## Findings
1. Non-preset workload runs reported the raw path string while preset runs used repo-relative paths, which made comparison artifacts feel inconsistent.
2. The HTML dashboard metadata listed the preset and timing knobs but omitted the actual algorithm set, which weakened screenshot usefulness when someone selected a subset.

## Fixes made
- normalized non-preset workload source paths through the same repo-relative helper used for presets
- added the selected algorithm list to the HTML dashboard metadata block
