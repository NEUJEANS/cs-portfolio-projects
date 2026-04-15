# Chord DHT resilience slice — review pass 1

## Focus
Execution sanity and regression coverage.

## Checks run
- `python3 -m unittest tests/test_chord_dht_lab.py`

## Issue found
- Initial resilience expectations were written against assumed node order instead of the ring's hashed clockwise order, so successor-list/failover assertions were wrong.

## Fix applied
- Updated the tests to assert the actual hash-derived node order and failover chain.
- Re-ran the project test suite successfully.
