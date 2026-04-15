# Chord DHT hop benchmark review — pass 3

## Focus
Explainability of benchmark output for portfolio readers.

## Issue found
- The benchmark summary reported counts and routes, but it did not include the ring's node list, which made standalone JSON snapshots less self-describing during review.

## Fix applied
- Added the current ring node list to benchmark output.
- Extended the benchmark unit test to assert that node metadata is included.

## Result
- Benchmark exports are easier to interpret when shared in docs, screenshots, or interview walkthroughs.
