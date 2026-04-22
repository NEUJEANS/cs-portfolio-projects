# Distance Vector Failure Benchmark Review — Pass 1

## Focus
Benchmark metric quality.

## Finding
The first benchmark draft reported only `max_cost_seen`, but every failed route eventually reaches infinity, so that metric hid the interesting count-to-infinity peak.

## Fix applied
- added `max_finite_cost_seen` to preserve the highest non-infinite transient metric
- updated the benchmark summary and rendered tables to use that more meaningful signal
- adjusted tests to compare finite peaks instead of the inevitable infinity endpoint

## Verification
- `python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py`
