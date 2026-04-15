# Review pass 2 — network-flow Dinic benchmark

Focus: benchmark design and regression coverage.

## Checks run
- `python3 projects/network-flow-lab/network_flow.py benchmark --nodes 24 --edge-probability 0.18 --trials 5 --seed 42 --pretty`
- `python3 projects/network-flow-lab/network_flow.py benchmark --nodes 60 --edge-probability 0.12 --trials 5 --seed 42 --pretty`
- `python3 -m py_compile projects/network-flow-lab/network_flow.py tests/test_network_flow_lab.py`

## Findings
- The parity guard worked: both algorithms agreed on max-flow values across all generated trials.
- On these small-to-medium pure-Python DAG benchmarks, Dinic was not consistently faster.
- Fix made: removed README wording that implied Dinic would necessarily be faster and reframed the benchmark as an algorithm trade-off comparison.
