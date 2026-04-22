# distance-vector-routing-lab

A compact Python simulator for Bellman-Ford-style distance-vector routing, including split horizon, poison reverse, and link-failure reconvergence.

## Why it is interesting
- shows how decentralized routers converge by exchanging only neighbor knowledge rather than building a full global graph
- demonstrates classic networking failure modes and the mitigation techniques interviewers often ask about
- makes dynamic routing behavior inspectable through round-by-round JSON history instead of opaque packet traces
- gives you a practical distributed-systems project that sits between graph algorithms and full network emulators

## Features
- symmetric weighted-topology input via JSON
- deterministic round-based convergence history with active-router scheduling metadata
- three advertisement modes: `classic`, `split-horizon`, and `poison-reverse`
- link-removal event simulation that can continue from the converged pre-failure state
- explicit `periodic` vs `triggered` update scheduling modes for comparing propagation behavior
- optional silent-router outage simulation with learned-route aging and timeout invalidation
- classic count-to-infinity behavior vs split-horizon / poison-reverse mitigation
- Markdown or Mermaid timeline export for per-round failure reconvergence artifacts
- failure benchmark mode that compares reconvergence behavior across routing modes and periodic vs triggered propagation
- JSON, CSV, or Markdown benchmark/report output suitable for docs, screenshots, notebooks, or lightweight visualizers
- validations for malformed or asymmetric topologies

## Usage

Simulate steady-state convergence on a small topology:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py simulate \
  --topology '{"A":{"B":1,"D":4},"B":{"A":1,"C":2},"C":{"B":2,"D":1},"D":{"A":4,"C":1}}'
```

Switch to poison reverse to discuss route advertisement behavior:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py simulate \
  --mode poison-reverse \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}'
```

Switch from full-round periodic propagation to event-driven triggered updates and inspect `history[*].active_routers` to see which router advertised each step:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py simulate \
  --mode classic \
  --update-strategy triggered \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}'
```

Remove a link and inspect reconvergence before vs after the event. The `after.history` timeline starts from the already-converged routing tables, so classic mode can visibly count upward toward the infinity metric:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py simulate-failure \
  --mode classic \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}' \
  --remove-link B C \
  --update-strategy triggered \
  --max-rounds 20
```

Treat one router as silent after convergence and let learned routes age out when refreshes stop arriving:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py simulate-outage \
  --mode classic \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}' \
  --silent-routers B \
  --route-timeout 2 \
  --max-rounds 4
```

Export that same failure as a portfolio-friendly round-by-round timeline for destination `C`:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py export-timeline \
  --mode classic \
  --format markdown \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}' \
  --remove-link B C \
  --destination C \
  --routers A B \
  --max-rounds 20
```

Benchmark that failure across classic, split-horizon, and poison-reverse with both periodic and triggered propagation strategies:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py benchmark-failure \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}' \
  --remove-link B C \
  --router A \
  --destination C \
  --format markdown \
  --max-rounds 20
```

Checked-in sample benchmark artifacts for that scenario live under:
- `artifacts/distance-vector-routing-lab/failure-benchmark.json`
- `artifacts/distance-vector-routing-lab/failure-benchmark.csv`
- `artifacts/distance-vector-routing-lab/failure-benchmark.md`

## Diagram export

Render the input topology as Mermaid for markdown-native docs:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py export-diagram \
  --topology '{"A":{"B":1,"D":4},"B":{"A":1,"C":2},"C":{"B":2,"D":1},"D":{"A":4,"C":1}}' \
  --snapshot topology \
  --format mermaid
```

Render the final routing table from one router as Graphviz DOT:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py export-diagram \
  --topology '{"A":{"B":1,"D":4},"B":{"A":1,"C":2},"C":{"B":2,"D":1},"D":{"A":4,"C":1}}' \
  --snapshot routes \
  --format dot \
  --router A
```

Use Mermaid when you want diagrams that render directly in GitHub markdown, and DOT when you want a richer graph-rendering pipeline later.

## Output shape

Steady-state runs return mode/config metadata, the normalized topology snapshot, final routing tables, and full round history. Each history entry now includes `active_routers` so you can tell whether the run used broad periodic rounds or narrower triggered propagation steps:

```json
{
  "converged": true,
  "mode": "classic",
  "rounds": 2,
  "tables": {
    "A": {
      "C": {
        "cost": 3,
        "destination": "C",
        "next_hop": "B"
      }
    }
  }
}
```

Failure runs wrap a stable pre-failure snapshot plus a reconvergence run that starts from those previously learned routes on the broken topology. That makes count-to-infinity behavior visible in classic mode instead of hiding it behind a fresh post-failure recomputation.

The failure benchmark command condenses that reconvergence history into one row per mode/update-strategy pair. It tracks one router/destination path, reports when the watched route first changes, when it first becomes unreachable, how high the finite metric climbs before stabilization, and which configuration settles fastest.

## Test

```bash
python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py
```

## Interview talking points
- why distance-vector routing can be implemented with only neighbor-to-neighbor table exchange
- how Bellman-Ford appears in distributed form rather than as a single centralized shortest-path pass
- what split horizon suppresses and what poison reverse actively advertises as unreachable
- how periodic full-table rounds differ from triggered route-change propagation
- why round snapshots are useful for deterministic tests and teaching demos
- how periodic vs triggered propagation changes reconvergence work even when final routes match
- how failure benchmarks make loop-mitigation trade-offs concrete instead of anecdotal
- how failure-driven reconvergence reveals more systems understanding than a static shortest-path answer

## Future improvements
- render neighbor-to-neighbor advertisement messages explicitly, not only final per-round tables
- add a built-in count-to-infinity sample scenario file plus checked-in timeline artifacts
- add per-route timeout / garbage-collection timers closer to RIP behavior
- extend the failure benchmark to run larger topology suites automatically
