# Static-site-generator comparison blocks review — pass 3

## Focus
Presentation polish in dark mode plus resumability/audit artifacts for the slice.

## Issues found
- The dark-theme CSS overrode comparison-panel eyebrow colors with a neutral shade, which muted the before/after/delta tone cues that the panels were supposed to preserve.
- The slice still lacked dedicated checklist/research notes, making later resumptions or audits harder than the other recent project slices.

## Fix applied
- Adjusted the comparison-panel styling so panel eyebrows and titles inherit the tone-specific color variables while the block-level eyebrow keeps its neutral dark-theme treatment.
- Added `docs/checklists/2026-04-17-static-site-generator-comparison-blocks-slice.md` and `docs/research/2026-04-17-static-site-generator-comparison-blocks.md`.
- Re-ran the project test suite after the styling update.

## Result
- Dark-mode comparison panels keep clearer visual distinction, and the slice now has the same resumable paper trail as the neighboring portfolio-project runs.
