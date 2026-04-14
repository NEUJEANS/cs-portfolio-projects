# Vector Clock Lab Review Pass 1

## Checks
- read implementation for causal-order correctness
- ran `python3 -m unittest discover -s projects/vector-clock-lab -p 'test_*.py' -v`

## Issues found
1. The initial test suite used pytest, but pytest was not available in the environment, which made the default test command fail.

## Fixes applied
- rewrote the suite to stdlib `unittest` so the project stays runnable with no extra dependency install
- updated the documented test command accordingly

## Result
- tests now run successfully in the default environment
