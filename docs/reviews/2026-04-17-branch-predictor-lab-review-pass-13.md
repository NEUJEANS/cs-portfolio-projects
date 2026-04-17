# branch-predictor-lab review pass 13

## Focus
Committed artifact-path consistency after the final smoke run.

## Issue found
The final smoke initially regenerated `tournament-style-comparison.{md,svg}` from a generic `artifacts/branch-predictor-lab/tournament-style.trace` path, while the gallery index and trace-setup notes already documented the seeded committed input as `artifacts/branch-predictor-lab/tournament-style-seed5.trace`.

## Fix applied
- regenerated the tournament comparison Markdown/SVG cards from `artifacts/branch-predictor-lab/tournament-style-seed5.trace`
- removed the accidental duplicate `tournament-style.trace` smoke artifact so the committed artifact set stays deterministic
- rechecked the generated Markdown headline/path and SVG XML validity after the rerender

## Result
The gallery, trace-setup docs, and committed comparison cards now all point at the same seeded trace input.
