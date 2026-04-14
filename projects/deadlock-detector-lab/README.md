# deadlock-detector-lab

A compact operating-systems portfolio project that detects deadlocks from either an explicit wait-for graph or a resource-allocation snapshot.

## Why it is interesting
- demonstrates classic OS concepts that come up in systems and interview discussions
- includes both graph-based cycle detection and multi-resource progress simulation
- produces machine-readable JSON output that is easy to test, demo, and extend

## Features
- analyze a wait-for graph with one concrete deadlock cycle
- analyze multi-instance resource allocation states using `available`, `allocation`, and `request` vectors
- report finish order for safe processes and resource shortages for blocked ones
- validate malformed inputs with clear errors

## Usage

Analyze a wait-for graph:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-wait \
  projects/deadlock-detector-lab/sample_wait_graph.json
```

Analyze a resource-allocation snapshot:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-allocations \
  projects/deadlock-detector-lab/sample_allocation_state.json
```

## Test

```bash
python3 -m unittest projects/deadlock-detector-lab/test_deadlock_detector.py
```

## Future improvements
- export Graphviz `.dot` output for visualization
- add step-by-step traces that show how the `work` vector evolves
- extend the project with deadlock avoidance examples such as Banker's algorithm
