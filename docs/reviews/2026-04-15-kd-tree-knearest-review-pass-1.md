# Review Pass 1 — KD-Tree k-Nearest Slice

## Focus
- CLI behavior and expected output ordering

## Issue found
- the new `knearest` CLI test expected `e` before `f` for query `(7, 2)`, but `f` is the exact match and must rank first

## Fix applied
- corrected the CLI expectation so the ranked output matches distance-first ordering with deterministic tie-breaking
