# Disk Scheduler LOOK / C-LOOK Review — Pass 1

## Focus
Algorithm correctness when the requested direction starts on an empty side of the disk.

## Findings
1. The first LOOK/C-LOOK refactor exposed an existing edge-case gap: non-circular SCAN behavior regressed when there were no pending requests in the current direction.
2. Upward SCAN with only lower requests and downward SCAN with only higher requests both need to preserve the physical boundary sweep for the original algorithms, while LOOK/C-LOOK should reverse or wrap immediately.

## Fixes made
- restored boundary sweeps for SCAN when the active side is empty
- added explicit upward-empty and downward-empty regression tests so SCAN/C-SCAN and LOOK/C-LOOK stay separated correctly
