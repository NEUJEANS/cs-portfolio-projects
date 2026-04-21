# CPU Scheduler Simulator Review — 2026-04-21 Fairness Pass 2

## Focus
SVG artifact resilience for larger presets and future workloads.

## Finding
The legend used a single fixed row, so larger workloads would eventually push process chips off the right edge of the SVG.

## Fix made
- made the SVG legend wrap to additional rows once it approaches the right edge, keeping the artifact readable as process counts grow
