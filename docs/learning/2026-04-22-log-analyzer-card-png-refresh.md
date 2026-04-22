# Refresh / self-test — 2026-04-22 — log-analyzer card PNG exports

## Quick refresh
- Reuse the existing card HTML renderers as the raster source so PNG exports cannot drift from the shipped HTML artifacts.
- Prefer one shared headless-Chrome screenshot path for both trend cards and comparison cards instead of duplicating browser command logic.
- When a PNG is requested without a matching HTML output path, write a temporary self-contained HTML file, capture it, and clean it up automatically.

## Self-test plan
1. Add shared Chrome-resolution/screenshot helpers plus CLI flags for trend-card and comparison-card PNG exports.
2. Extend tests for command wiring, PNG validation errors, and at least one real CLI PNG capture path when Chrome is available locally.
3. Regenerate committed sample PNG artifacts from the existing annotated sample cards and verify they open as non-empty PNG files.
4. Finish with py_compile, unittest, real CLI smoke runs, and three focused review passes.
