# 2026-04-14 Disk Scheduler Lab Review Pass 2

## Focus
Developer experience and reproducibility.

## What I checked
- README test command
- sample input file usability
- CLI compare output shape

## Issues found
1. README originally used a pytest command, but this repo environment does not guarantee pytest.

## Fixes made
- updated the README to use the built-in `python3 -m unittest` command
- reran the project test suite with the documented command
