# Chord DHT hop benchmark review — pass 2

## Focus
Benchmark input hygiene and summary correctness.

## Issue found
- Repeating `--start-node` values could duplicate benchmark cases and distort the summary totals, even though the caller likely meant to benchmark each start node once.

## Fix applied
- Deduplicated optional benchmark start nodes while preserving their original order.
- Expanded the benchmark test to verify duplicate start-node requests collapse into a single case set.

## Result
- Benchmark summaries stay fair and deterministic even when the CLI receives repeated start-node flags.
