# Consistent Hashing Virtual-Node Benchmark Report

Deterministic benchmark summary for the consistent-hashing lab. It turns the JSON benchmark series into a recruiter-friendly table so load-balance and remap tradeoffs are readable without extra scripting.

- Physical nodes: 3 (node-a, node-b, node-c)
- Keys: 5000
- Replication factor: 2
- Topology change: add `node-d`
- Best imbalance ratio: 1.032 at `128` virtual nodes per physical node

## Benchmark series

| Virtual nodes | Max load | Min load | Average load | Imbalance ratio | Moved keys | Movement ratio | Replica placement changes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 4959 | 1968 | 3333.3333 | 1.4877 | 2699 | 0.5398 | 5398 |
| 8 | 3912 | 2765 | 3333.3333 | 1.1736 | 2548 | 0.5096 | 5096 |
| 32 | 3501 | 3130 | 3333.3333 | 1.0503 | 2477 | 0.4954 | 4954 |
| 128 | 3440 | 3177 | 3333.3333 | 1.032 | 2554 | 0.5108 | 5108 |

## Takeaways

- The most balanced tested ring used `128` virtual nodes per physical node, with an imbalance ratio of `1.032`.
- At that setting, the load range was `3177` to `3440` around an average of `3333.3333` keys per physical node.
- Under the tested topology change, the best-balance configuration moved `2554` keys, a movement ratio of `0.5108`, with `5108` replica-placement changes.
