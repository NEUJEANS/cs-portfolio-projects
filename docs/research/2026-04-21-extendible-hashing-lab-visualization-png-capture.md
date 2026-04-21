# Extendible hashing lab visualization PNG capture research — 2026-04-21

## Why this slice needed research
The visualization flow already exported rich SVG/HTML artifacts plus a compact thumbnail strip, but the README still lacked a no-manual-screenshot path for the full split/merge walkthrough. The question was whether the benchmark dashboard's Chrome-headless pattern was also a good fit for the workload visualization page.

## Brief findings
- Chrome Headless officially supports `--screenshot`, and the docs explicitly recommend pairing it with `--window-size`, which fits this repo's self-contained visualization HTML well.
- `--dump-dom` is also officially supported, which makes it a reasonable lightweight way to probe rendered document height before taking the screenshot.
- The visualization page is fully self-contained (`file://` safe, no network assets), so reusing the benchmark PNG approach avoids introducing Playwright/Selenium or a second rendering stack.
- Repo-local precedent already exists in the same lab for benchmark PNG export, so matching that contract keeps the project easier to explain and maintain.

## Sources checked
- Chrome Headless docs: https://developer.chrome.com/docs/chromium/headless
- repo-local precedent: `projects/extendible-hashing-lab/extendible_hashing_lab.py` benchmark PNG helpers
- repo-local precedent: `projects/tarjan-scc-lab/tarjan_scc_lab.py`

## Decision
Add an optional `visualize --png-out` flow that requires `--html-out`, reuses the existing Chrome-headless screenshot pattern, auto-sizes the screenshot height for multi-step workload pages, and regenerates committed PNG artifacts for both the sample and delete-heavy visualization stories.
