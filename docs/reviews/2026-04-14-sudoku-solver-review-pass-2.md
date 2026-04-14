# 2026-04-14 sudoku-solver review pass 2

## Focus
CLI execution path and regression smoke tests.

## Findings
- an edit artifact duplicated the CLI footer and left a broken `return` outside `main`, causing a syntax error

## Fixes
- removed the duplicated trailing block and restored a single clean `if __name__ == '__main__': raise SystemExit(main())` entrypoint

## Validation
- `python3 -m unittest discover -s projects/sudoku-solver -p 'test_*.py'` -> pass
- solved puzzle smoke test with `--compact` -> pass
