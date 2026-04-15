# Chord synthetic benchmark review pass 1 — 2026-04-15

## Checks run
- `python3 -m unittest tests/test_chord_dht_lab.py`
- `python3 -m py_compile projects/chord-dht-lab/chord_dht.py`
- `python3 projects/chord-dht-lab/chord_dht.py synth-benchmark --m-bits 9 --nodes 12 --keys 15 --seed 23 --start-nodes 4`

## Issue found
- Synthetic generation did not explicitly reject non-positive `m_bits`, which could lead to invalid ring-size behavior before generation.

## Fix applied
- Added `m_bits` validation in `build_synthetic_benchmark_payload`.
- Added unit coverage for invalid synthetic benchmark parameters.

## Result
- Pass 1 complete after fix; tests and smoke checks pass.
