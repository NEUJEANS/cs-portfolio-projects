# Review pass 1 - algorithm and metadata audit

## Focus
- verify subtree-size updates across insertion and rotations
- verify validation catches augmentation drift

## Findings
1. `select` raised a raw `IndexError` to the terminal when the CLI received an out-of-range index.

## Fixes applied
- wrapped command dispatch in `main()` so `IndexError` becomes an argparse error with a clean message
- added a CLI regression test for out-of-range `select`

## Result
- order-statistics metadata remains consistent after balancing
- CLI behavior is safer for invalid user input
