# deadlock-detector-lab

A compact operating-systems portfolio project that detects deadlocks from either an explicit wait-for graph or a resource-allocation snapshot, and now also demonstrates Banker's algorithm for deadlock avoidance.

## Why it is interesting
- demonstrates classic OS concepts that come up in systems and interview discussions
- includes graph-based cycle detection, multi-resource progress simulation, and Banker's algorithm safety checks
- adds step-by-step Banker's safety and request traces for portfolio demos
- produces machine-readable JSON output that is easy to test, demo, and extend

## Features
- analyze a wait-for graph with one concrete deadlock cycle
- analyze multi-instance resource allocation states using `available`, `allocation`, and `request` vectors
- report finish order for safe processes and resource shortages for blocked ones
- analyze a Banker's algorithm state using `available`, `allocation`, and `max`
- emit step-by-step Banker's trace steps with runnable sets, `work` vectors, and released allocations
- export Banker's safety and request demos as Markdown artifacts with `--markdown-out`
- evaluate whether a proposed resource request should be granted or denied safely
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

Analyze whether a Banker's algorithm state is safe:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-banker \
  projects/deadlock-detector-lab/sample_banker_state.json
```

Export a recruiter-friendly Banker's safety trace:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-banker \
  projects/deadlock-detector-lab/sample_banker_state.json \
  --markdown-out docs/artifacts/deadlock-detector-lab/sample_banker_trace.md
```

Evaluate whether a proposed request should be granted:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py request-banker \
  projects/deadlock-detector-lab/sample_banker_request.json
```

Export a Banker's request trial trace:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py request-banker \
  projects/deadlock-detector-lab/sample_banker_request.json \
  --markdown-out docs/artifacts/deadlock-detector-lab/sample_banker_request_trace.md
```

## JSON formats

Banker's algorithm safety analysis expects:

```json
{
  "available": {"A": 3, "B": 3, "C": 2},
  "allocation": {
    "P0": {"A": 0, "B": 1, "C": 0}
  },
  "max": {
    "P0": {"A": 7, "B": 5, "C": 3}
  }
}
```

`analyze-banker` and `request-banker` JSON output now also includes `trace_steps`, and unsafe states additionally report `blocking` shortages so the stalled processes are easy to explain.

Banker's algorithm request evaluation adds:

```json
{
  "process": "P1",
  "request": {"A": 1, "B": 0, "C": 2}
}
```

## Test

```bash
python3 -m unittest projects/deadlock-detector-lab/test_deadlock_detector.py
```

## Future improvements
- export Graphviz `.dot` output for wait-for and resource-allocation visualization
- compare deadlock detection and avoidance results side-by-side in one report
- add SVG or HTML visual summaries on top of the new Banker's trace exports
