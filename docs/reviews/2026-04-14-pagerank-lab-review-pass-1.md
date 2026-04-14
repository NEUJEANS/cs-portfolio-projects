# Review Pass 1 - PageRank Lab

## Checks
- ran the CLI against the sample graph
- verified whether the sample actually demonstrated dangling-node behavior
- inspected output fields for recruiter/demo usefulness

## Issue found
- the original sample graph had no true dangling node, which weakened the main teaching point.

## Fix applied
- changed the sample graph to include a real sink node
- added a regression test for the sample sink node
- exposed `score_sum` in rank output to make normalization easy to verify in demos
