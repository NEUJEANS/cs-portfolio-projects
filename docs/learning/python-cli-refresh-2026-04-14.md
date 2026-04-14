# Python CLI Refresh - 2026-04-14

## Refresher
- `argparse` is enough for a portfolio-quality standard-library CLI when the command tree is modest.
- `dataclasses` keep domain objects small and explicit.
- `tempfile` + `Path.replace()` gives a simple atomic write path for JSON persistence.
- `unittest` with isolated temp directories is enough for reliable CLI integration tests.

## Tiny self-test
1. Can `argparse` subcommands share common flags? Yes, via parent parsers or repeated additions.
2. What avoids partial JSON writes? Write temp file first, then replace the target.
3. Best fit for ISO date parsing here? `date.fromisoformat()` with validation.

## Result
Refresher complete; no extra training needed before implementation.
