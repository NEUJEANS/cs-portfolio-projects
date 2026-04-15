# Review pass 1 — fenwick-tree-range-query-lab

## Focus
Core correctness for Fenwick construction, range updates, and range sums.

## What I checked
- unit test run against the new project
- range-add behavior versus expected raw values
- snapshot reload behavior after updates

## Issue found
- `RangeFenwick.__post_init__` built the structure by calling the public `range_add` method, which also mutated `values`, so initial values were effectively applied twice.

## Fix applied
- introduced `_range_add_internal` for tree-only updates during initialization
- rebuilt the initial structure from a copied original value list

## Result
- correctness bug fixed and tests now pass for the original failing scenarios
