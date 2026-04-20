# MVCC isolation lab timeline/SVG refresh + self-test — 2026-04-20

## Quick refresh
- a transaction timeline SVG only needs a few primitives: lane rectangles, tick grid lines, event cards, and text labels
- because one schedule tick can emit both `begin` + first step or final step + `commit`, same-tick events must stack within a lane instead of drawing at the exact same coordinates
- committed-version callouts should live in a separate band so readers can see which commits advanced the visible database state

## Self-test
1. What bug appears if every event at a tick uses the same lane coordinates?
   - `begin` and first-step cards, or final-step and commit cards, overlap and hide each other.
2. What keeps the export easy to host in GitHub Pages or recruiter docs?
   - emit a self-contained SVG with inline styles and no external assets.
3. What should a good summary line include for this lab?
   - isolation level, final version, final state, and invariant status.

## Guardrails
- preserve the existing JSON/text CLI output; add SVG as an optional export, not a replacement
- keep filenames deterministic for compare-mode batch exports so committed artifacts stay easy to diff
- test both renderer content and CLI file creation paths
