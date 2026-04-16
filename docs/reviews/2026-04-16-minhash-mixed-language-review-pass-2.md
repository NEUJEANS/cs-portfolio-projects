# Review pass 2 — MinHash mixed-language preset

## Focus
Safety and resumability for repeated demo generation.

## Findings
1. The preset workflow needed an explicit regression check that a second write without `--force` fails instead of silently overwriting files.

## Fixes
- Added a unit test covering the existing `FileExistsError` guard for repeat preset writes.
