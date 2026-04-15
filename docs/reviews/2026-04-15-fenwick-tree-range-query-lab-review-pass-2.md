# Review pass 2 — fenwick-tree-range-query-lab

## Focus
Input validation and snapshot robustness.

## What I checked
- snapshot schema validation
- newline-delimited input parsing behavior
- edge cases that could produce confusing errors in demos

## Issues found
- snapshot validation accepted JSON booleans because `bool` is a subclass of `int` in Python
- invalid input lines would raise a plain integer-conversion error without line context

## Fix applied
- tightened snapshot validation to require `type(value) is int`
- added line-number-aware error reporting in `load_values`
- added tests covering both cases

## Result
- validation errors are clearer and demo failures are easier to diagnose
