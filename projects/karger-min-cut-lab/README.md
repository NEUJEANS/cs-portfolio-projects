# Karger Min Cut Lab

A portfolio-friendly randomized algorithms project that implements Karger's random contraction algorithm for the global minimum cut of a small undirected multigraph, with deterministic seeds, repeated trials, contraction traces, and benchmark artifacts across multiple graph families.

## Why this project is portfolio-worthy
- demonstrates a classic randomized graph algorithm instead of another deterministic data-structure exercise
- gives you a clean way to discuss probability, repetition, and algorithmic confidence in interviews
- shows careful engineering around reproducibility by supporting deterministic seeded runs
- includes exact or family-aware cut verification so the randomized result can be validated in tests and demos
- surfaces contraction traces and benchmark artifacts that make the algorithm easier to explain on slides or a whiteboard

## Features
- undirected multigraph loader from JSON
- single-trial and multi-trial Karger runs
- deterministic sequential seeds for reproducible repeated trials
- optional contraction trace for the first reported trial
- exact min-cut checker for small graphs to validate randomized runs
- built-in benchmark mode across cycle, complete, barbell, and Erdos-Renyi graph families
- JSON and CSV output suitable for automation, README embeds, and future chart rendering

## Project structure
- `karger_min_cut.py` - graph model, randomized contraction engine, exact checker, graph-family builders, and CLI
- `sample_graph.json` - small demo graph for reproducible experiments
- `test_karger_min_cut.py` - unit and CLI coverage

## Usage
```bash
python3 projects/karger-min-cut-lab/karger_min_cut.py demo --trials 8 --seed 7 --exact-check --pretty
python3 projects/karger-min-cut-lab/karger_min_cut.py run --graph-file projects/karger-min-cut-lab/sample_graph.json --trials 20 --seed 11 --include-trace --exact-check --pretty
python3 projects/karger-min-cut-lab/karger_min_cut.py benchmark \
  --families cycle,complete,barbell,erdos-renyi \
  --sizes 4,6,8 \
  --instances-per-size 2 \
  --trials 32 \
  --seed 17 \
  --output-json artifacts/karger-min-cut-benchmark.json \
  --output-csv artifacts/karger-min-cut-benchmark.csv \
  --pretty
```

## Benchmark artifact snapshot
Committed artifacts from the latest benchmark slice:
- `artifacts/karger-min-cut-benchmark.json`
- `artifacts/karger-min-cut-benchmark.csv`

Current family summary (`32` trials per instance, two instances per size):
- cycle: hit rate `1.0`, average best cut `2.0`
- complete: hit rate `1.0`, average best cut `5.0`
- barbell: hit rate `1.0`, average best cut `1.0`
- Erdos-Renyi: hit rate `1.0`, average best cut `1.0`

This is intentionally a small, portfolio-friendly benchmark. The point is to show how repeated trials and graph structure interact, not to claim an exhaustive experimental study.

Notes:
- `--sizes` means vertex count for cycle/complete/Erdos-Renyi families.
- For the `barbell` family, each size value is the clique size on each side, so total vertices are `2 * size`.

## Testing
```bash
python3 -m unittest discover -s projects/karger-min-cut-lab -p 'test_*.py' -v
```

## Interview talking points
- why random edge contraction preserves the true minimum cut with non-zero probability
- why one run is not enough, and why repeated trials improve confidence
- how deterministic seeding helps debugging without changing the algorithmic idea
- why parallel edges matter after contractions and why self-loops must be removed
- why graph-family benchmarks help explain when a randomized algorithm looks deceptively strong on small inputs
- when you should switch from a randomized contraction approach to a deterministic min-cut algorithm

## Future improvements
- compare Karger with Stoer-Wagner or max-flow-based exact min cut on the same inputs
- emit Graphviz snapshots after each contraction for richer visual demos
- render the CSV benchmark artifact into a small Markdown or image chart for README embedding
