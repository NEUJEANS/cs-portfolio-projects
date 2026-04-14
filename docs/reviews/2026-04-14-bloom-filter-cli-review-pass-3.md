# bloom-filter-cli review pass 3 — 2026-04-14

## Focus
Portfolio quality: demo value, docs, and measurable tradeoff reporting.

## Findings
1. Binary export without a size comparison would undersell the benefit.
2. The README needed concrete numbers to make the tradeoff legible to reviewers.

## Fixes made
- Added `compare-sizes` command for standard vs. counting JSON/binary artifact comparison.
- Added benchmark-sized artifact numbers and usage examples to the project README.
