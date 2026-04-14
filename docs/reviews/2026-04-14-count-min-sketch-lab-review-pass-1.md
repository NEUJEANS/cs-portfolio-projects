# Review pass 1 — count-min-sketch-lab

## Focus
Correctness of the new memory benchmark implementation.

## Issue found
- `deep_size_bytes()` initially counted only the shallow size of custom objects, so `sketch_full_bytes` could incorrectly appear smaller than the sketch core tables.

## Fix applied
- Extended recursive sizing to include `__dict__` for custom objects, which makes the full sketch size reflect the contained config, tables, counters, and metadata.

## Validation
- Re-ran the pytest suite after the fix and confirmed the CLI benchmark test now passes.
