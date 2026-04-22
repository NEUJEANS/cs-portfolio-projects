# Distance Vector Failure Benchmark Review — Pass 3

## Focus
Portfolio discoverability and repo-level regression safety.

## Finding
The feature worked, but the README did not point readers to checked-in sample artifacts, which made the new benchmark less useful as a portfolio showcase without rerunning the CLI.

## Fix applied
- documented the checked-in benchmark artifact paths in the project README
- generated JSON, CSV, and Markdown sample artifacts for the canonical `A-B-C` failure scenario
- reran the project-specific and repo-wide test suites

## Verification
- `python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
