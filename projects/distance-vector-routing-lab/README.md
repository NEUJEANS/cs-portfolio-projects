# distance-vector-routing-lab

A compact Python simulator for Bellman-Ford-style distance-vector routing, including split horizon, poison reverse, and link-failure reconvergence.

## Why it is interesting
- shows how decentralized routers converge by exchanging only neighbor knowledge rather than building a full global graph
- demonstrates classic networking failure modes and the mitigation techniques interviewers often ask about
- makes dynamic routing behavior inspectable through round-by-round JSON history instead of opaque packet traces
- gives you a practical distributed-systems project that sits between graph algorithms and full network emulators

## Features
- symmetric weighted-topology input via JSON
- deterministic round-based convergence history
- three advertisement modes: `classic`, `split-horizon`, and `poison-reverse`
- link-removal event simulation to study reconvergence after failures
- JSON output suitable for docs, screenshots, notebooks, or lightweight visualizers
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

Remove a link and inspect reconvergence before vs after the event:

```bash
python3 projects/distance-vector-routing-lab/distance_vector_routing.py simulate-failure \
  --mode poison-reverse \
  --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}' \
  --remove-link B C
```

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

Steady-state runs return mode/config metadata, the normalized topology snapshot, final routing tables, and full round history:

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

Failure runs wrap two simulations so you can compare the stable network before the event and the final tables after the removed link.

## Test

```bash
python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py
```

## Interview talking points
- why distance-vector routing can be implemented with only neighbor-to-neighbor table exchange
- how Bellman-Ford appears in distributed form rather than as a single centralized shortest-path pass
- what split horizon suppresses and what poison reverse actively advertises as unreachable
- why round snapshots are useful for deterministic tests and teaching demos
- how failure-driven reconvergence reveals more systems understanding than a static shortest-path answer

## Future improvements
- add topology import/export for Graphviz or Mermaid diagrams
- render per-round advertisement traces to make loop behavior easier to visualize
- compare convergence length across modes on larger benchmark scenarios
