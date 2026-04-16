# Mini MapReduce plugin docs pages self-test

Date: 2026-04-16 21:00 UTC
Project: `mini-mapreduce-lab`

## Refresh
- `os.path.relpath(target, start=base)` is the simplest reliable way to emit portable links between a shared catalog index and generated per-plugin pages, even when the output directory is user-specified.
- Reusing the existing plugin slug (`plugin_anchor_id`) for filenames keeps page names deterministic across runs and aligned with the in-page anchor scheme already used by the catalog reports.
- When generating both Markdown and HTML sidecars, each page should link to its sibling format with just the basename while linking back to the catalog via a relative path from the page directory.
- For publishable human-facing artifacts, plugin file references should be repo-relative (`projects/...`) rather than absolute workstation paths, even if the inspection JSON keeps the resolved absolute path for machine-readable consumers.

## Quick self-check
- If `report-output` is `/tmp/plugin-catalog.md` and `docs-dir` is `/tmp/plugin-pages`, the Markdown catalog should link to `plugin-pages/plugin-average-score.md`.
- The generated Markdown plugin page should link back to `../plugin-catalog.md`, and the generated HTML plugin page should link back to `../plugin-catalog.html`.
- Keeping filename generation slug-based avoids path drift between quick-link cards, page filenames, and future docs-site routing.
