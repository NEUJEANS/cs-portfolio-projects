# 2026-04-16 distributed snapshot SVG assets research

## Goal
Finish the next distributed-snapshot presentation slice by turning the generated walkthrough into reusable SVG files that work in GitHub docs, slide decks, and portfolio pages.

## Why this is the right next slice
- The lab already exports Mermaid and a committed Markdown walkthrough, so the weakest remaining gap is reusable rendered artwork.
- SVG is a good first target because it stays text-based, deterministic in git, and easy to embed from Markdown.
- Committed per-snapshot assets make the partition/heal scenario easier to reuse in project pages without manual screenshot work.

## Asset requirements
- derive each SVG from the same structured snapshot result used by the walkthrough so the export stays reproducible
- include the timeline cues that matter most in interviews: transfers, failures, recoveries, markers, balances, channel state, and consistency totals
- keep filenames deterministic so generated docs can link to committed assets safely
- make the CLI capable of writing Markdown and SVG in one run so the repo stays resumable

## Chosen implementation direction
- add a pure-Python SVG renderer for one snapshot at a time
- add a helper that writes one SVG per captured snapshot with stable slugged filenames
- teach `walkthrough` to embed relative links/images to those generated SVG files when `--svg-dir` is provided
- leave PNG as a later follow-up instead of adding a new raster dependency in this slice
