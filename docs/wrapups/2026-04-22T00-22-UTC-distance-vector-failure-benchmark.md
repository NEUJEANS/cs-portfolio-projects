# Distance Vector Failure Benchmark Wrap-up

- Timestamp: 2026-04-22 00:22 UTC
- Project: `distance-vector-routing-lab`
- Implementation commit: `901b850` (`feat(distance-vector-routing-lab): add failure benchmark reports`)

## What changed
- added a `benchmark-failure` command to compare link-failure reconvergence across classic, split-horizon, and poison-reverse modes with periodic or triggered propagation
- tracked watched-route metrics such as first change, first unreachable round, last route-change round, and highest finite transient cost
- added JSON, CSV, and Markdown benchmark renderers plus checked-in sample artifacts for the canonical `A-B-C` failure scenario
- expanded README usage/docs and recorded research, refresh, checklist, and three review-pass notes for resumability

## Tests and reviews run
- `python3 -m unittest projects/distance-vector-routing-lab/test_distance_vector_routing.py`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 projects/distance-vector-routing-lab/distance_vector_routing.py benchmark-failure --topology '{"A":{"B":1},"B":{"A":1,"C":1},"C":{"B":1}}' --remove-link B C --router A --destination C --max-rounds 20 --format json`
- review pass 1: replaced misleading `max_cost_seen` interpretation with `max_finite_cost_seen`
- review pass 2: deduplicated repeated mode/update-strategy selections
- review pass 3: documented checked-in artifacts and regenerated sample outputs
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail` (0 verified, 0 unknown)

## Next step
- extend the benchmark beyond the tiny `A-B-C` loop into a small curated scenario suite so the project can compare mitigation behavior on richer topologies too
