# network-flow-lab review pass 3 — 2026-04-16

## Focus
Benchmark CLI failure-mode audit.

## Issue found
The new `dense` and `layered` benchmark families have minimum node-count requirements, but invalid combinations surfaced as raw Python tracebacks instead of clean CLI feedback.

## Fix
- added benchmark CLI validation that checks shared generator inputs before execution
- added family-specific `--nodes` validation with a direct argparse error message
- added regression coverage for both the programmatic `ValueError` path and the CLI error output
- clarified the README family descriptions with the minimum node requirements

## Result
Invalid benchmark-family invocations now fail fast with a readable CLI error, which makes the lab friendlier for portfolio demos and screenshot-driven usage.
