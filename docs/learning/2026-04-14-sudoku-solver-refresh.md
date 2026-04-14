# 2026-04-14 sudoku-solver refresh and self-test

## Refresh
- Python `argparse` for mutually simple CLI inputs
- recursive backtracking patterns with helper functions that stay pure/testable where possible
- set-based duplicate detection for row/column/3x3 validation

## Self-test
### Q1
Why is MRV useful in a Sudoku solver?

### A1
It chooses the next empty cell with the fewest legal values, which usually finds contradictions earlier and reduces wasted branching.

### Q2
Why validate the initial board before solving?

### A2
A contradictory board can never become valid, so fast validation avoids misleading output and unnecessary recursion.

### Q3
What should a good CLI solver distinguish?

### A3
At least three states: invalid input, valid-but-unsolved/unsatisfiable puzzle, and solved puzzle.
