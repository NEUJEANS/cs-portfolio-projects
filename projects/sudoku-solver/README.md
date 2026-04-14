# sudoku-solver

## Overview
Solve 9x9 Sudoku boards from the command line using MRV-guided backtracking and board validation.

## Why this is a stronger portfolio project
- demonstrates recursive search plus a classic CSP-style heuristic instead of only naive brute force
- validates malformed or contradictory boards before search starts
- supports compact string input or board files with `0` / `.` placeholders
- exposes clean exit codes for solved, unsolved, and invalid-input workflows

## Stack
- Python
- no extra runtime dependency required for the default path

## Features
- parses 81-cell compact inputs or text files with whitespace/newlines while rejecting stray non-board characters
- validates row, column, and 3x3 box constraints before solving
- uses MRV (minimum remaining values) to choose the next empty cell
- prints either a readable grid or compact solved string output
- returns exit code `0` for solved, `1` for no-solution puzzles, and `2` for invalid input/file errors

## Usage
```bash
python3 sudoku_solver.py 530070000600195000098000060800060003400803001700020006060000280000419005000080079
python3 sudoku_solver.py --compact 530070000600195000098000060800060003400803001700020006060000280000419005000080079
python3 sudoku_solver.py --file puzzle.txt
```

Example `puzzle.txt`:
```text
53..7....
6..195...
.98....6.
8...6...3
4..8.3..1
7...2...6
.6....28.
...419..5
....8..79
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Brief implementation notes
- keeps parsing/validation separate from solving so tests can target each layer
- MRV candidate selection reduces branching by solving the most constrained cell first
- explicit error messages make the CLI easier to automate and demo

## Future Improvements
- add optional explanation mode that shows placements/backtracks for learning/demo use
- benchmark naive search vs MRV on a small puzzle corpus
- support puzzle generation and difficulty scoring
