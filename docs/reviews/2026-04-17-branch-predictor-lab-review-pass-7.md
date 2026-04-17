# branch-predictor-lab review pass 7

## Focus
Refresh-note and resumability audit after adding local-history and tournament predictors.

## Issue found
The existing self-test note still stopped at bimodal + gshare coverage, so the project memory for future slices was stale relative to the new advanced predictors.

## Fix applied
- updated `docs/learning/2026-04-17-branch-predictor-self-test.md`
- added local-history and tournament refresh points
- added explicit self-test targets for correlated mixed traces and JSON state inspection

## Result
Future runs now have an accurate learning/self-test handoff for the advanced predictor slice.
