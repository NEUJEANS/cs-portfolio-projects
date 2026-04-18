# Learning refresh — 2026-04-18 — page-replacement gallery slice

## Quick rules refresher
- A good static artifact gallery should work as plain HTML with no build step.
- Each chart card should use `<figure>` with a first- or last-child `<figcaption>` so the chart and its caption stay grouped semantically.
- Inline SVG charts should keep explicit `<title>` and `<desc>` metadata.
- When multiple SVGs appear on the same page, their `id` values must stay unique so `aria-labelledby` and `aria-describedby` references do not collide.
- Companion files should stay predictable and machine-friendly, so per-preset stems like `<preset>-study.{md,svg,csv,json}` are easier to link and regenerate.

## Self-test
For a gallery covering the built-in presets over frames `2..6`, I expect:
- `classic-belady` to show a FIFO anomaly and a Clock regression at `3 -> 4`
- the other built-in presets to stay monotonic for FIFO and Clock in this default frame range
- OPT to win the average-fault summary across all four built-in workloads in the current preset set
- the generated HTML to embed multiple inline SVG charts without duplicated accessibility IDs

## Implementation note
Prefer a single `gallery` command that writes the HTML page and the per-preset companion studies together, so regenerating the committed bundle stays one command instead of a fragile multi-step doc workflow.
