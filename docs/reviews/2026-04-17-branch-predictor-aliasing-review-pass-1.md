# 2026-04-17 branch predictor aliasing review pass 1

## Focus
Code-path review for the new alias summary and artifact-talking-point flow.

## Issue found
- The new aliasing insight was appended after the older label-summary point, so the top-5 talking points could omit aliasing entirely on the new alias-thrash artifact.

## Fix applied
- Reordered `_build_comparison_talking_points()` so aliasing insights are emitted before the generic top-label summary.
- Re-rendered the alias-thrash Markdown/SVG artifacts after the fix.

## Result
- The alias-thrash card now surfaces the aliasing story in the recruiter-facing talking points instead of hiding it below the cut.
