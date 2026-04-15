# Chord DHT lab review — pass 3

## Focus
Docs/usage consistency after the implementation changes.

## Issue found
- The README and research note originally described the bundled ring with a 5-bit example, which no longer matched the corrected 8-bit fixture.

## Fix applied
- Updated the README ring example and research note to document the 8-bit demo choice and its purpose.
- Re-ran the project CLI commands and full test suite to confirm the docs reflect working commands.

## Result
- The project is internally consistent across implementation, fixtures, docs, and tests.
