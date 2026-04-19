# Research — 2026-04-19 — log-analyzer facet detail bundles

## Goal
Turn the existing facet-ranking gallery into a handoff-friendly packet that reviewers can download, unzip, and browse slice by slice without losing links back to the main gallery.

## Quick findings
- Python's `zipfile` docs make `ZipInfo(..., date_time=...)` plus `ZipFile.writestr(...)` the simplest standard-library path for deterministic archive members.
- The docs also confirm that archive member names are explicit strings, so stable ordering + fixed timestamps/permissions are enough to keep regenerated ZIP bytes predictable for Git diffs and review handoffs.
- That fits this project well because the analyzer already has deterministic facet card IDs and portable relative-link rewriting; the missing piece was packaging focused pages and metadata together.

## Sources checked
- Python docs — `zipfile`: https://docs.python.org/3/library/zipfile.html

## Slice decision
Implement `--facet-ranking-detail-bundle-dir` so one facet-ranking run can emit:
- `index.html`
- `manifest.json`
- one `slices/<card-id>.html` page per facet slice
- a deterministic `facet-ranking-detail-bundle.zip`

## Why this slice
It upgrades the portfolio story from “here is a large gallery” to “here is a portable review packet” — a more realistic artifact for release reviews, asynchronous handoffs, and recruiter-friendly screenshots.