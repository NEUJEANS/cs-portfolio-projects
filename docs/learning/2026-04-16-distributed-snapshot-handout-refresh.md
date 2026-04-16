# 2026-04-16 distributed snapshot handout refresh

## Quick refresh
- A single-file HTML handout is a good fit here because the walkthrough data is already structured: summary cards, ordered timeline items, snapshot metadata, and asset references can all be rendered deterministically from one result object.
- `<picture>` is a practical way to prefer committed SVG diagrams while still falling back to PNG assets for viewers or slide tools that handle raster images more reliably.
- Relative asset links should be resolved from the handout file location, not from the current working directory, so committed docs remain portable when viewed locally or on GitHub Pages-style static hosting.
- When the CLI mixes an absolute `--html-output` path with relative asset directories, normalize the asset path against the process working directory before computing the final handout-relative href; otherwise the HTML can accidentally embed machine-specific absolute path fragments.

## Self-test
1. **Why keep Markdown walkthrough output even after adding HTML?**  
   Because Markdown stays diff-friendly and GitHub-native, while HTML serves as the polished single-page presentation layer.

2. **When both SVG and PNG assets exist, which should the handout prefer?**  
   Prefer SVG for crisp scaling, but keep the PNG path available as a fallback/openable asset.

3. **What makes the handout resumable instead of hand-crafted?**  
   It is rendered from the same tested walkthrough result object that already drives the Markdown export and asset generation.
