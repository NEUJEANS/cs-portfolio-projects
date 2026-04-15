# Chord Graphviz review pass 2

## Focus
Automated coverage and payload shape.

## Findings
1. New functionality lacked direct tests for ring/route/stabilization DOT output.
2. Demo payload should advertise the new visualization artifact.

## Fixes applied
- Added unit tests for all three export modes.
- Added CLI test coverage for `graphviz` route export.
- Added `graphviz_preview` to the demo payload.
