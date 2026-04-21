# Research — robin-hood-hashing-lab PNG export — 2026-04-21

## Goal
Add a repeatable PNG export for the benchmark dashboard without making the screenshot so tall that it becomes useless in a portfolio deck.

## References checked
1. Repo-local reference: `projects/tarjan-scc-lab/tarjan_scc_lab.py`
   - already ships a Chrome/Chromium headless screenshot path with binary discovery, viewport sizing, and CLI validation.
   - confirmed the repo already has a proven pattern for `--png-output` style artifact capture.
2. Repo-local reference: `projects/tarjan-scc-lab/README.md`
   - documents the user-facing contract that PNG capture should pair with HTML export and allow an explicit browser binary override.
3. Local tool check: `google-chrome --version`
   - confirmed the host already has a working headless-capable Chrome binary for real smoke validation.

## Design takeaways
- Reuse the repo’s existing Chrome discovery and headless screenshot pattern instead of inventing a second PNG workflow.
- Keep `--png-out` dependent on `--html-out` so the PNG remains a companion artifact, not a separate reporting pipeline.
- Use a compact screenshot mode for PNG capture.
  - The full HTML dashboard is too tall to make a good single-image artifact.
  - Hiding lower-priority sections during the PNG capture keeps the exported bitmap recruiter-friendly while leaving the full HTML artifact unchanged.
- Keep viewport controls exposed (`--png-width`, `--png-height`, `--png-capture-ms`, `--chrome-binary`) so reruns stay debuggable.
