# File Integrity Monitor Review Pass 2

## Focus
CLI usability and resumability.

## Findings
1. `scan --output nested/path/baseline.json` would fail if the parent directory did not already exist.

## Fixes Applied
- create parent directories automatically before writing a baseline manifest.
- expanded CLI coverage to test writing a baseline into a nested directory.

## Result
- the project is easier to use in fresh workspaces and scripted runs.
