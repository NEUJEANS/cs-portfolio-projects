# Review log — two-phase-commit-lab timeline PNG/social-preview slice — 2026-04-21

## Pass 1 — API + code-path review
- Checked the new PNG export wiring across `terminate`, catalog generation, and related-artifact links.
- Issue found: the new `--timeline-png-width` / `--timeline-png-height` flags did not actually influence the rendered preview canvas, only the Chrome viewport.
- Fix: thread the requested width/height into `render_termination_resolution_timeline_social_preview_html()` and the PNG renderer so the preview layout matches the requested capture size.

## Pass 2 — docs + UX review
- Reviewed README and CLI discoverability for the new PNG export.
- Issue found: the first README draft showed `--timeline-png-out` but did not explain the framing knobs or custom Chrome path.
- Fix: added follow-up CLI guidance in the README and clarified that the PNG is a compact social-preview cover while the SVG/HTML remain the full-detail artifacts.

## Pass 3 — rendered artifact review
- Smoke-tested `terminate --timeline-png-out ...` and inspected the generated PNG with vision review.
- Issue found: the first preview layout was too tall for 1280x640, causing a white-block cutoff near the bottom of the cards.
- Fix: compacted the preview layout, shortened preview-card copy, removed preview footers from the rendered PNG card strip, and revalidated the regenerated artifact until the clipping disappeared.

## Validation run after fixes
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- `python3 projects/two-phase-commit-lab/two_phase_commit_lab.py terminate projects/two-phase-commit-lab/coordinator_crash_partial_commit_delivery.json --timeline-png-out /tmp/two_phase_partial_timeline.png`
- regenerated committed catalogs/artifacts under `docs/artifacts/two-phase-commit-lab/`
