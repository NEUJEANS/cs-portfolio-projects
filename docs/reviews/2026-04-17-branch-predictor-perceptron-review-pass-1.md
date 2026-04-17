# 2026-04-17 branch predictor perceptron review pass 1

## Focus
Artifact-gallery discoverability for the new perceptron slice.

## Issue found
- The new `perceptron-majority` trace and comparison files existed locally, but the branch-predictor gallery still only showed the older sample, tournament-style, and alias-thrash cards.

## Fix applied
- Added `perceptron-majority-comparison.{md,svg}` to `docs/artifacts/branch-predictor-lab/index.md`.
- Added trace-setup notes for the seeded committed input `artifacts/branch-predictor-lab/perceptron-majority-seed13.trace`.
- Added a short portfolio-usage note explaining what the new card demonstrates.

## Result
- The perceptron slice is now discoverable from the portfolio gallery instead of looking like an orphaned artifact.
