# Chord DHT lab review — pass 2

## Focus
CLI/demo behavior and test reliability.

## Issue found
- The CLI demo test implicitly assumed the `compiler` sample assignment would always appear at a fixed list index, which was brittle because assignments are sorted by key identifier.

## Fix applied
- Changed the test to map sample assignments by key name before comparing the lookup owner.
- Kept the CLI payload shape unchanged so the demo remains simple for users.

## Result
- The test now validates the actual ownership relationship instead of depending on incidental ordering.
