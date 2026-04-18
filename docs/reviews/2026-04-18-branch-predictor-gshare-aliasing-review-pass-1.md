# 2026-04-18 branch predictor dynamic gshare aliasing review pass 1

## Focus
Recruiter-facing comparison-card talking points after the new dynamic gshare alias summary landed.

## Issue found
- The new dynamic gshare insight was appended after the hardest-branch note, so the top-5 talking points on the Markdown/SVG cards could still omit the new feature entirely.

## Fix applied
- Reordered `_build_comparison_talking_points()` so static and dynamic aliasing insights are emitted before the lower-priority hardest-branch note.
- Re-rendered the committed comparison artifacts after the ordering change.

## Result
- The alias-focused cards now surface both static and dynamic interference in the top-level talking points instead of burying the new slice below the cutoff.
