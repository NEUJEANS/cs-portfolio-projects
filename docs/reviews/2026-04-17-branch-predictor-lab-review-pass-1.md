# Branch-predictor-lab review — pass 1

## Focus
Implementation correctness and predictor-behavior sanity checks.

## Issue found
- The first comparison-table example drafted for the README did not match the simulator's real output on `sample_trace.txt`, which would have made the project look untrustworthy during a demo.

## Fix applied
- Ran the real `compare` CLI against the checked-in sample trace.
- Updated the README example table to match the actual current output.

## Result
- The docs now reflect the current implementation instead of an invented example.
