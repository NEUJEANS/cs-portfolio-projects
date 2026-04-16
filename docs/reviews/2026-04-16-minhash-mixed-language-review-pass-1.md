# Review pass 1 — MinHash mixed-language preset

## Focus
Feature completeness and CLI ergonomics.

## Findings
1. `--normalize-literals` help text still said numeric-only literals even though the implementation also normalizes strings, booleans, and `None`.

## Fixes
- Updated the CLI help text to describe the broader literal normalization behavior accurately.
