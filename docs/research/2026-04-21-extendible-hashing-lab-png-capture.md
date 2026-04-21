# Extendible hashing lab PNG capture research — 2026-04-21

## Why this slice needed research
The remaining checklist item was a compact benchmark-dashboard screenshot export, and the repo already had a strong static HTML dashboard. The open question was whether the safest implementation was a direct browser CLI capture or a heavier rendering dependency.

## Brief findings
- Chrome Headless officially supports `--screenshot` and explicitly calls out pairing it with `--window-size`, which fits this repo's self-contained local HTML dashboard well.
- `--virtual-time-budget` is a lightweight way to let any layout/paint work settle before capture without adding Playwright/Selenium to a small portfolio lab.
- Local `file://...` URLs are enough here because the dashboard uses inline CSS and does not rely on network assets.
- Repo-local precedent already exists in `tarjan-scc-lab`, so matching that pattern reduces surprise and keeps maintenance simpler across projects.

## Sources checked
- Chrome Headless docs: https://developer.chrome.com/docs/chromium/headless
- repo-local precedent: `projects/tarjan-scc-lab/tarjan_scc_lab.py`
- quick grounding search for `Google Chrome headless screenshot --screenshot --window-size --virtual-time-budget documentation`

## Decision
Add an optional `benchmark --png-out` flow that requires `--html-out`, resolves a local Chrome/Chromium binary only when PNG capture is requested, estimates a tall-enough viewport for the dashboard, and captures the checked-in benchmark dashboard PNG from the generated HTML artifact.
