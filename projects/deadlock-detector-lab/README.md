# deadlock-detector-lab

A compact operating-systems portfolio project that detects deadlocks from either an explicit wait-for graph or a resource-allocation snapshot, and now also demonstrates Banker's algorithm for deadlock avoidance.

## Why it is interesting
- demonstrates classic OS concepts that come up in systems and interview discussions
- includes graph-based cycle detection, multi-resource progress simulation, and Banker's algorithm safety checks
- adds step-by-step Banker's safety and request traces for portfolio demos
- exports SVG and HTML visuals for wait-for, resource-allocation, and Banker's walkthroughs
- builds one combined detection-vs-avoidance dashboard so the two detection models, the primary Banker's request trace, and an optional granted-vs-denied delta callout can be shown together
- produces machine-readable JSON output that is easy to test, demo, and extend

## Features
- analyze a wait-for graph with one concrete deadlock cycle
- analyze multi-instance resource allocation states using `available`, `allocation`, and `request` vectors
- report finish order for safe processes and resource shortages for blocked ones
- export wait-for and resource-allocation visuals as SVG and HTML artifacts
- analyze a Banker's algorithm state using `available`, `allocation`, and `max`
- emit step-by-step Banker's trace steps with runnable sets, `work` vectors, and released allocations
- export Banker's safety and request demos as Markdown, SVG, and HTML artifacts
- evaluate whether a proposed resource request should be granted or denied safely
- compare granted and denied request trials with delta-focused callouts for lost slack and runnable options
- validate malformed inputs with clear errors

## Usage

Analyze a wait-for graph:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-wait \
  projects/deadlock-detector-lab/sample_wait_graph.json
```

Export wait-for visuals:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-wait \
  projects/deadlock-detector-lab/sample_wait_graph.json \
  --svg-out docs/artifacts/deadlock-detector-lab/sample_wait_graph.svg \
  --html-out docs/artifacts/deadlock-detector-lab/sample_wait_graph.html
```

Analyze a resource-allocation snapshot:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-allocations \
  projects/deadlock-detector-lab/sample_allocation_state.json
```

Export resource-allocation visuals:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-allocations \
  projects/deadlock-detector-lab/sample_allocation_state.json \
  --svg-out docs/artifacts/deadlock-detector-lab/sample_allocation_state.svg \
  --html-out docs/artifacts/deadlock-detector-lab/sample_allocation_state.html
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

Export static Banker's safety visuals:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py analyze-banker \
  projects/deadlock-detector-lab/sample_banker_state.json \
  --svg-out docs/artifacts/deadlock-detector-lab/sample_banker_trace.svg \
  --html-out docs/artifacts/deadlock-detector-lab/sample_banker_trace.html
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

Export static Banker's request visuals:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py request-banker \
  projects/deadlock-detector-lab/sample_banker_request.json \
  --svg-out docs/artifacts/deadlock-detector-lab/sample_banker_request_trace.svg \
  --html-out docs/artifacts/deadlock-detector-lab/sample_banker_request_trace.html
```

Compare safe and unsafe Banker's request trials side by side, including delta-focused callouts:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py compare-banker-requests \
  projects/deadlock-detector-lab/sample_banker_request.json \
  projects/deadlock-detector-lab/sample_banker_request_unsafe.json \
  --markdown-out docs/artifacts/deadlock-detector-lab/sample_banker_request_gallery.md \
  --html-out docs/artifacts/deadlock-detector-lab/sample_banker_request_gallery.html \
  > docs/artifacts/deadlock-detector-lab/sample_banker_request_gallery.json
```

Build one combined dashboard for the wait-for graph, allocation snapshot, and Banker's traces, optionally threading in a granted-vs-denied request delta:

```bash
python3 projects/deadlock-detector-lab/deadlock_detector.py dashboard \
  --wait-input projects/deadlock-detector-lab/sample_wait_graph.json \
  --allocation-input projects/deadlock-detector-lab/sample_allocation_state.json \
  --banker-input projects/deadlock-detector-lab/sample_banker_state.json \
  --banker-request-input projects/deadlock-detector-lab/sample_banker_request.json \
  --banker-contrast-input projects/deadlock-detector-lab/sample_banker_request_unsafe.json \
  --markdown-out docs/artifacts/deadlock-detector-lab/sample_detection_vs_avoidance_dashboard.md \
  --html-out docs/artifacts/deadlock-detector-lab/sample_detection_vs_avoidance_dashboard.html
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
- export Graphviz `.dot` output for teams that want to post-process the same layouts externally
- add a multi-request dashboard mode that compares more than one risky request pair in the same one-page story
