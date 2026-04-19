# Regex engine benchmark tag-filter slice research — 2026-04-19

## Brief refresh
- No external web research was necessary for this slice; the needed decisions were local CLI/data-contract choices rather than new algorithm work.
- The existing regex benchmark path already separates suite loading, case execution, and Markdown/JSON rendering, so tag-based filtering can stay a thin layer over the current benchmark workflow.
- A single committed workload file becomes more portfolio-friendly if it can drive both a tiny interview demo and a broader benchmark batch without duplicating near-identical JSON files.

## Slice decision
Add optional per-case `tags` plus repeatable `--include-tag` / `--exclude-tag` benchmark filters for built-in and JSON-backed suites.

Why this is the right next slice:
- it directly finishes the follow-up left by the previous benchmark-suite run
- it improves the portfolio story by letting one workload bundle support multiple demo sizes
- it stays bounded to CLI/reporting work while still producing visible committed artifacts and a better reviewer workflow
