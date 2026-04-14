# PageRank Lab

A graph-algorithms project that computes PageRank scores for a local directed graph, reports convergence details, and highlights dangling-node handling in a recruiter-friendly CLI.

## Why this project is portfolio-worthy
- demonstrates graph modeling, iterative numerical computation, and ranking-system intuition
- turns a classic search/systems concept into a practical local tool with tests
- gives clear interview material around damping, teleportation, convergence, and sink handling
- stays lightweight: pure Python, no third-party dependencies required

## Features
- edge-list parser for local graph files
- iterative PageRank engine with configurable damping, tolerance, and iteration limits
- explicit handling for dangling nodes so probability mass stays normalized
- JSON CLI output with full scores, top-k rankings, convergence metrics, and score normalization
- graph inspection command for node/edge counts and outgoing-link structure

## Project structure
- `pagerank_lab.py` - graph parser, PageRank engine, and CLI
- `test_pagerank_lab.py` - unit + CLI tests
- `sample_graph.txt` - small demo graph with a dangling node and a self-looping node

## Usage
Run from this directory.

### Inspect a graph
```bash
python3 pagerank_lab.py inspect sample_graph.txt
```

### Compute ranks and show the top 3 nodes
```bash
python3 pagerank_lab.py rank sample_graph.txt --top 3
```

### Tune convergence settings
```bash
python3 pagerank_lab.py rank sample_graph.txt --damping 0.9 --max-iterations 200 --tolerance 1e-10
```

## Testing
```bash
python3 -m unittest discover -s projects/pagerank-lab -p 'test_*.py' -v
```

## Interview talking points
- why PageRank uses damping instead of trusting links completely
- how dangling nodes can leak or trap rank mass if you do not redistribute them
- what convergence tolerance means and why iteration limits still matter
- how sorting top-k output deterministically improves demos and regression tests

## Future improvements
- add personalized PageRank with a seed distribution
- support CSV/JSON graph import formats
- compare PageRank against in-degree ranking on the same graph
- export results as Markdown tables or simple HTML reports
