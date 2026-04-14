# Flashcard Quiz App Review Pass 2

## Focus
Session flow correctness for shuffle/limit/retry behavior.

## Checks
- verified seeded shuffle is deterministic in tests
- verified `--limit` slices after shuffle for reproducible short study rounds
- verified retry mode only re-asks missed cards once
- verified summary reports attempts separately from unique-card count

## Findings
No additional defects found after the new test coverage and manual diff review.

## Result
The new study-session flow is coherent and demo-friendly.
