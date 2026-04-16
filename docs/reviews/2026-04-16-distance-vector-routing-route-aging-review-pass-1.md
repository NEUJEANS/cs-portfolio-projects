# Distance Vector Routing Route Aging Review — Pass 1

## Focus
CLI surface and test harness sanity for the route-aging outage slice.

## Findings
1. `simulate-outage` was handled in `cli()` but missing from `argparse`, so the new mode was unreachable from the command line.
2. `test_distance_vector_routing.py` ended with a stray `main()` call, causing the module import to fail before tests could run.

## Fixes applied
- Added a real `simulate-outage` subcommand with mode/timeout/update options.
- Removed the stray `main()` call so the unittest module imports cleanly.

## Verification
- Re-ran `python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py`.
