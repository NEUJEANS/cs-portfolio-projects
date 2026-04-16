# Review pass 2 — graph-routing Mermaid slice

## Focus
CLI and artifact usability review.

## Issues found
1. The project had no direct way to emit a reusable graph artifact from the command line.

## Fixes applied
- Added `--export-mermaid` so the lab can generate `.mmd` artifacts during demos, docs generation, or automation runs.
- Emitted a sample artifact to `docs/artifacts/graph-routing-negative-cycle-sample.mmd`.
