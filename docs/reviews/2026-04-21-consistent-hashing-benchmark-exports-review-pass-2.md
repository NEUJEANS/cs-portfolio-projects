# 2026-04-21 consistent-hashing benchmark exports review pass 2

## Focus
Check whether the new feature is discoverable and usable from the project README.

## Issue found
- The implementation added `--csv-out` and `--markdown-out`, but the README initially did not show an export example, artifact paths, or what each flag produced.

## Fix applied
- Added a benchmark export usage example to the README.
- Documented the new CSV and Markdown export flags in the notes section.
- Added a sample committed artifacts section so the new outputs are easy to find later.

## Verification
- README command examples were checked against the implemented CLI flags.
