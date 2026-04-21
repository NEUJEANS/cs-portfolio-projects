# CPU Scheduler Simulator Review — 2026-04-21 Fairness Pass 1

## Focus
Whether the new SVG made the worst fairness tails obvious at a glance.

## Finding
The first draft kept SVG rows in PID order, which made the worst-off process harder to spot quickly inside each algorithm block.

## Fix made
- sorted each SVG chart block by the active metric descending so the heaviest slowdown or waiting burden appears first for every algorithm
