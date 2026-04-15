# Karger Min Cut Lab

A portfolio-friendly randomized algorithms project that implements Karger's random contraction algorithm for the global minimum cut of a small undirected multigraph, with deterministic seeds, repeated trials, contraction traces, and an optional exact verifier for small graphs.

## Why this project is portfolio-worthy
- demonstrates a classic randomized graph algorithm instead of another deterministic data-structure exercise
- gives you a clean way to discuss probability, repetition, and algorithmic confidence in interviews
- shows careful engineering around reproducibility by supporting deterministic seeded runs
- includes an exact cut checker for small graphs so the randomized result can be validated in tests and demos
- surfaces contraction traces that make the algorithm easier to explain on slides or a whiteboard

## Features
- undirected multigraph loader from JSON
- single-trial and multi-trial Karger runs
- deterministic sequential seeds for reproducible repeated trials
- optional contraction trace for the first reported trial
- exact min-cut checker for small graphs to validate randomized runs
- JSON CLI output suitable for automation and demos

## Project structure
- `karger_min_cut.py` - graph model, randomized contraction engine, exact checker, and CLI
- `sample_graph.json` - small demo graph for reproducible experiments
- `test_karger_min_cut.py` - unit and CLI coverage

## Usage
```bash
python3 projects/karger-min-cut-lab/karger_min_cut.py demo --trials 8 --seed 7 --exact-check --pretty
python3 projects/karger-min-cut-lab/karger_min_cut.py run --graph-file projects/karger-min-cut-lab/sample_graph.json --trials 20 --seed 11 --include-trace --exact-check --pretty
```

## Testing
```bash
python3 -m unittest discover -s projects/karger-min-cut-lab -p 'test_*.py' -v
```

## Interview talking points
- why random edge contraction preserves the true minimum cut with non-zero probability
- why one run is not enough, and why repeated trials improve confidence
- how deterministic seeding helps debugging without changing the algorithmic idea
- why parallel edges matter after contractions and why self-loops must be removed
- when you should switch from a randomized contraction approach to a deterministic min-cut algorithm

## Future improvements
- add a benchmark that measures success rate versus trial count on several graph families
- compare Karger with Stoer-Wagner or max-flow-based exact min cut on the same inputs
- emit Graphviz snapshots after each contraction for richer visual demos
