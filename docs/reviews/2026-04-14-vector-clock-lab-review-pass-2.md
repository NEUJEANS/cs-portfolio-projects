# Vector Clock Lab Review Pass 2

## Checks
- reviewed constructor and merge semantics for invalid input handling
- ran `python3 -m py_compile projects/vector-clock-lab/vector_clock_lab.py`
- ran `python3 -m unittest discover -s projects/vector-clock-lab -p 'test_*.py' -v`

## Issues found
1. ReplicaStore silently deduplicated repeated replica names, which could hide bad test setups or confusing CLI inputs.
2. Conflict merge relied on current store state implicitly instead of validating that the stored versions were genuinely concurrent.

## Fixes applied
- changed replica initialization to reject duplicate names explicitly
- added an explicit concurrency check before merge proceeds
- added a unit test covering duplicate replica rejection

## Result
- invalid topology inputs now fail fast
- merge behavior better matches the distributed-systems concept being demonstrated
