# Log Analyzer Upgrade Research — 2026-04-14

## Goal
Upgrade `projects/log-analyzer` from a minimal counter into a more interview- and portfolio-ready CLI.

## Practical feature targets
- parse a structured access-log shape instead of loose substring matching
- summarize HTTP status codes and methods
- show hot paths and top client IPs
- track malformed lines so quality issues are visible
- support machine-readable output for automation

## Chosen slice for this run
Implement a parser for common access-log lines, add richer summary metrics, add text/JSON CLI output, and expand tests.

## Deferred follow-ups
- combined-log parsing with referrer and user-agent
- response-time latency summaries if timing fields are present
- CSV export or richer filtering
