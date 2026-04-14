# Review Pass 2 - PageRank Lab

## Checks
- reread README against CLI behavior
- reviewed argument validation and output consistency
- confirmed project can be explained without reading source first

## Issue found
- `--top` was documented as a positive count, but the command path did not reject non-positive values explicitly.

## Fix applied
- added explicit `--top` validation in the rank command path
- kept output deterministic and JSON-friendly for demos/tests
