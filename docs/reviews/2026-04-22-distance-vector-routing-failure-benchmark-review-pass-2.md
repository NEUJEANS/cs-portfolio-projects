# Distance Vector Failure Benchmark Review — Pass 2

## Focus
CLI/input robustness.

## Finding
Repeated `--modes` or `--update-strategies` arguments could generate duplicate benchmark rows, which would make checked-in reports noisy and harder to compare.

## Fix applied
- deduplicated requested modes and update strategies while preserving the caller's order
- added regression coverage for duplicate benchmark selections

## Verification
- `python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py`
