# 2026-04-17 branch predictor perceptron review pass 3

## Focus
README reproducibility and smoke-test alignment.

## Issue found
- README showed how to benchmark a temporary `/tmp/perceptron-majority.trace`, but it did not show the exact seeded commands that regenerate the committed gallery artifact paths used by the docs.

## Fix applied
- Added a committed-path reproduction example to `projects/branch-predictor-lab/README.md` for `perceptron-majority-seed13.trace` and its Markdown/SVG outputs.
- Re-ran the focused compare smoke check and SVG XML parse against the committed artifact files.

## Result
- The public docs now match the committed artifact set, and the perceptron slice can be reproduced without guessing filenames.
