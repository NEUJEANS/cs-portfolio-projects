# Python CLI Refresh — 2026-04-14

## Quick refresh used for this slice
- `argparse` subparsers keep a small CLI easy to grow.
- `dataclasses` make the task model compact and readable.
- Keeping domain logic separate from CLI printing makes tests much easier.
- `pathlib.Path` keeps file handling cleaner than string concatenation.

## Self-test
1. Why not store business logic directly inside argparse handlers?
   - It makes the code harder to test and easier to tangle with I/O.
2. Why use an atomic write pattern for JSON persistence?
   - It reduces the chance of leaving a corrupt data file if the process is interrupted.
3. Why keep filtering in a service layer instead of only in the CLI?
   - The behavior becomes reusable by tests and future interfaces.
