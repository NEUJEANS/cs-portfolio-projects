# Research — 2026-04-18 — log-analyzer hotspot filters slice

## Goal
Extend `projects/log-analyzer` so the per-path hotspot views can focus on incident-relevant subsets such as failing requests or POST-heavy write traffic.

## Quick findings
- The analyzer already parses both HTTP status and method on every valid line, so hotspot filtering can be implemented without changing the log parser shape.
- The most portfolio-friendly design is to keep the top-level totals and percentile summaries global, then apply optional filters only to the hotspot breakdowns and hotspot CSV exports.
- Self-describing exports matter for screenshots and spreadsheet follow-up work, so filtered CSVs should record which status/method drill-down produced them.

## Slice decision
Implement repeatable hotspot-only drill-down flags:
1. add `--hotspot-status` for one or more status codes
2. add `--hotspot-method` for one or more HTTP methods
3. annotate text/JSON/CSV hotspot outputs with the active filters
4. preserve existing unfiltered summaries so the command still shows the full traffic picture

## Why this slice
It turns the project from a generic traffic summarizer into something closer to a real incident-analysis tool: you can ask which failing endpoints are slow, or which POST-heavy flows are upstream-bound, without losing the surrounding operational context.
