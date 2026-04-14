# 2026-04-14 Disk Scheduler Lab Review Pass 1

## Focus
Algorithm edge cases and boundary behavior.

## What I checked
- FCFS, SSTF, SCAN, and C-SCAN ordering for the classic sample workload
- downward sweep behavior when the initial direction has no pending requests
- empty-request handling

## Issues found
1. SCAN/C-SCAN incorrectly swept to a boundary even when there were zero requests.

## Fixes made
- added an early return so empty simulations keep the head at the start cylinder with zero movement
- added a regression test covering the empty-request case
