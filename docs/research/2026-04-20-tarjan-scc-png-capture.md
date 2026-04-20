# Tarjan SCC PNG capture research — 2026-04-20

## Why research was needed
The checklist already pointed to PNG/raster capture as the clearest unfinished Tarjan SCC follow-up, but I still needed one quick confirmation on the safest local implementation path.

## Brief findings
- Chrome/Chromium headless supports direct screenshots with `--headless` + `--screenshot=...`.
- `--window-size=WIDTH,HEIGHT` is the key knob for making the exported dashboard readable in slide-ready captures.
- `--hide-scrollbars` avoids ugly scrollbars in the committed artifact.
- `--virtual-time-budget=...` is a lightweight way to let local HTML settle before capture without adding a heavier browser automation dependency.
- Local `file://...` URLs are enough here because the benchmark dashboard is self-contained and uses inline CSS instead of network assets.

## Sources consulted
- Chrome headless docs / blog references surfaced via web search for `Google Chrome headless screenshot command --screenshot --window-size file URL documentation`
- validated locally with a direct `google-chrome --headless --disable-gpu --hide-scrollbars --window-size=1400,1800 --screenshot=... file:///.../sample-compare.html` smoke test before coding

## Decision
Use the installed local Chrome/Chromium binary via `subprocess.run(...)` instead of adding Playwright/Selenium or a new Python image-rendering dependency.
