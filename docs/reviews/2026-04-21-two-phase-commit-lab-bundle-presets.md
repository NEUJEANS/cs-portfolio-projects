# Review log — 2026-04-21 — two-phase-commit-lab bundle presets

## Pass 1 — preset flow and CLI/API shape
- checked that saved presets resolve through the existing tag-filter pipeline instead of duplicating selection logic
- issue found: preset-driven catalog artifact generation did not rebuild protocol-comparison artifacts for the blocked scenarios that already surface those links in the catalog
- fix: added `_should_generate_catalog_comparison(...)` inside `build_catalog_entries(...)` so preset bundle runs regenerate comparison Markdown/HTML whenever the scenario is a blocked case worth contrasting against saga behavior

## Pass 2 — recovery-story artifact UX
- inspected the `recovery-story` preset output after regeneration
- issue found: the catalog still invited readers to open the incident-response dashboard even though the preset contains `0 blocked` scenarios
- fix: gated the dashboard prompt in `render_catalog_markdown(...)` on `blocked_count > 0` while keeping the renderer itself safe for empty blocked-case bundles

## Pass 3 — deterministic artifact and docs verification
- reran the incident-review, recovery-story, full catalog, and peer-assisted catalog commands into committed artifact paths
- reran incident-review and recovery-story into a temporary directory, compared outputs with `cmp`, validated relative Markdown links, and ran `git diff --check`
- result: no further issues found after the fixes above
