# 2026-04-14 sudoku-solver upgrade research

## Goal
Turn `sudoku-solver` from a minimal backtracking script into a stronger portfolio project with better validation, clearer CLI behavior, and a more interview-ready search strategy.

## Brief notes from research
- backtracking is still the right baseline for a compact 9x9 solver
- MRV (minimum remaining values) is a strong low-complexity upgrade: choose the empty cell with the fewest legal candidates first
- validate the starting board before search so contradictory puzzles fail fast instead of recursing pointlessly
- keep row/column/box legality checks explicit and testable
- clear CLI error messages matter for portfolio polish and automation

## Slice selected for this run
1. add input parsing for compact strings and text files with `0`/`.` placeholders
2. validate board shape, cell ranges, and duplicate conflicts before solving
3. upgrade search to MRV-guided backtracking with candidate generation
4. improve CLI outputs and exit codes for solved / unsolved / invalid cases
5. expand tests and add checklist/review docs for resumability

## References consulted
- Peter Norvig Sudoku notes (`norvig.com/sudoku.html`) for CSP-style heuristics inspiration
- general MRV/backtracking/validation summaries surfaced via web search
