# CPU Scheduler Simulator Review — 2026-04-21 Fairness Pass 3

## Focus
Whether the Markdown and HTML fairness summaries exposed the same spread story as the SVG.

## Finding
The fairness snapshot listed average and max slowdown plus standard deviation, but it still hid the simple best-to-worst slowdown range that readers often look for first.

## Fix made
- added a dedicated slowdown-spread column to the Markdown and HTML fairness snapshot tables so the range between the best and worst per-process experience is explicit
