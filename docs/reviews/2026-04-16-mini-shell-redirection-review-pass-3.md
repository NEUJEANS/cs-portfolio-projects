# Mini Shell Redirection Review — Pass 3

## Findings
1. The README examples showed basic redirect support, but they did not explicitly show edge-of-pipeline file redirection or call out the builtin-stdin limitation.
2. Parser validation also needed a direct regression test for a dangling redirect operator.

## Fixes applied
- expanded the README session example to include pipeline-to-file output
- added notes clarifying the supported redirection boundaries for this focused slice
- added a regression test for `echo hello >` so the parser keeps the clear error message

## Result
The slice is easier to resume later because the docs now match the implementation boundaries and the parser failure mode is pinned by a focused test.
