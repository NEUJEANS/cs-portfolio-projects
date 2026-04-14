# mini-mapreduce-lab review pass 1

## Checks
- ran `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py`

## Issues found
- test module initially failed to import `mapreduce` because the project directory was not on `sys.path`

## Fixes applied
- inserted the project directory into `sys.path` inside the test file before importing `execute_job`
