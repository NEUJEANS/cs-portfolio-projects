# 2026-04-18 branch predictor dynamic gshare aliasing review pass 3

## Focus
Artifact-gallery consistency after the compare/sweep output format changed.

## Issue found
- The committed comparison cards and sweep report were still generated from the pre-gshare-aliasing output shape.
- The gallery index wording for `alias-thrash` only mentioned static table interference, which undersold the new dynamic-history story.

## Fix applied
- Re-ran the committed compare/sweep artifact commands for sample, tournament-style, alias-thrash, perceptron-majority, and the full trace-family sweep.
- Updated `docs/artifacts/branch-predictor-lab/index.md` so the alias-thrash usage note explicitly mentions dynamic gshare-history collisions.

## Result
- The gallery, README reproduction commands, and committed reports are aligned with the live CLI output and the new branch-predictor narrative.
