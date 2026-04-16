# Log Analyzer combined-log + latency research - 2026-04-16

## Goal
Strengthen `log-analyzer` so it can handle realistic access logs instead of only the bare common-log subset.

## Brief findings
- Apache combined logs extend the common format with quoted referrer and user-agent fields, so adding optional quoted tail parsing preserves backward compatibility with simpler logs.
- Apache commonly logs request duration with `%D` (microseconds), while Nginx-style access logs often append a decimal request time in seconds.
- Normalizing both styles into milliseconds keeps the JSON/text output easier to compare and turns latency metrics into something portfolio reviewers can read quickly.

## Scope chosen
- accept common logs, combined logs, and an optional trailing latency token in one parser
- summarize top referrers and user agents when present
- report latency aggregates/percentiles only when at least one parsed line includes a response-time field
