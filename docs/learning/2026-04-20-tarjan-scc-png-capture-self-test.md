# Tarjan SCC PNG capture self-test — 2026-04-20

- Goal: add a resumable PNG helper without changing the existing compare payload shape or introducing a new frontend stack.
- Refresher: the HTML dashboard is already the portfolio-friendly source of truth, so the PNG helper should layer on top of it rather than inventing a second report renderer.
- Refresher: viewport sizing matters more than image post-processing for this slice because the dashboard is fully static and already styled.
- Self-check notes:
  - require `--html-output` when `--png-output` is requested so the raster export clearly stays tied to the HTML artifact
  - auto-estimate a reasonable viewport height from trial/component counts, but keep width/height override flags for edge cases
  - keep the implementation dependency-light by resolving a local Chrome/Chromium binary and calling it directly
  - add unit tests for command construction and capture flow so the project stays stable even when the environment/browser path changes later
