# Review Pass 1 - link-state-routing-lab

## Focus
Core simulation correctness under tests.

## Issues found
1. `flood_lsas()` treated a mapping of LSAs as an iterable of keys, causing `str`/`router` attribute errors.
2. Heap ordering for simultaneous flood events compared `LinkStateAdvertisement` objects directly, causing a `TypeError`.

## Fixes applied
- Normalized `origin_lsas` so mappings use `.values()`.
- Added stable scalar tie-break fields (`router`, `sequence`) to heap entries.

## Verification
- `./.venv/bin/python -m pytest -q projects/link-state-routing-lab/test_link_state_routing.py`
- Result after fixes: passing.
