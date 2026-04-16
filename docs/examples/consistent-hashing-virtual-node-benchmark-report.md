# Consistent Hashing Virtual-Node Benchmark Example

Sample command:

```bash
python3 projects/consistent-hashing-lab/consistent_hashing.py benchmark \
  --nodes node-a node-b node-c \
  --key-count 5000 \
  --virtual-node-counts 1 8 32 128 \
  --add-node node-d
```

Sample highlights from the deterministic workload:

| virtual nodes | imbalance ratio | moved keys | movement ratio |
| --- | ---: | ---: | ---: |
| 1 | 1.8192 | 772 | 0.1544 |
| 8 | 1.2300 | 1919 | 0.3838 |
| 32 | 1.3122 | 1368 | 0.2736 |
| 128 | 1.0638 | 1287 | 0.2574 |

Takeaway:
- more virtual nodes substantially improved steady-state balance in this workload
- remap movement was not strictly monotonic across all counts, which is a useful interview talking point about ring geometry and workload shape
- the JSON output is structured so a later slice can export this series into charts or markdown summaries automatically
