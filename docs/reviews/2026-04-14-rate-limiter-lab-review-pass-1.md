# Review Pass 1 - Rate Limiter Lab

## Checks
- ran focused automated tests
- ran fixed-window CLI smoke test
- inspected core state transitions for each algorithm

## Issues found
1. tests initially depended on pytest, which is not guaranteed in this repo environment
2. project needed to stay runnable with a minimal standard-library setup

## Fixes made
- converted the test suite to stdlib `unittest`
- updated the README test command to use `python3 test_rate_limiter_lab.py`
