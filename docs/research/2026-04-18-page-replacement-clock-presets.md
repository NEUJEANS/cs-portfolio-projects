# Research — 2026-04-18 — page-replacement clock + presets slice

## Why this slice next
The initial page-replacement lab already covered FIFO, LRU, OPT, and FIFO anomaly studies, but it still lacked a more realistic online policy and a cleaner way to run repeatable workloads. Adding Clock / second-chance plus curated presets makes the project feel more like a polished systems lab instead of a one-off coding exercise.

## Brief external refresh
- reviewed Clock / second-chance behavior: circular hand, reference bit, clear-on-scan, evict-first-zero policy
- rechecked the stack-algorithm framing: LRU and OPT should stay monotonic as frames increase, while FIFO is the classic anomaly example
- picked preset families that highlight different locality patterns instead of only one textbook string:
  - `classic-belady`
  - `looping-hotset`
  - `scan-then-reuse`
  - `mixed-locality-bursts`

## Implementation goal
Ship one vertical slice that lets a student:
1. compare a practical Clock policy against FIFO / LRU / OPT,
2. reuse named workloads for demos and screenshots, and
3. study frame-count regressions without retyping long page strings.
