# Markdown Notes Search Section Refresh — 2026-04-15

## Goal
Refresh Markdown heading-anchor behavior before adding section-scoped retrieval.

## Quick reminders
- heading anchors should be deterministic and lowercase
- punctuation should be stripped before converting spaces to dashes
- duplicate headings need suffixes like `-1`, `-2` to keep anchors unique
- section content should stay scoped to the heading block instead of swallowing nested sibling sections

## Self-test
1. `## Failure Detection` -> `failure-detection`
2. second identical `## Failure Detection` in the same note -> `failure-detection-1`
3. `### Raft & Logs` -> `raft-logs`
4. when a query hits only a subsection body, the best result should expose `path#anchor` for direct navigation

## Outcome
Ready to add note sections to the JSON index and surface best-match anchors in text/JSON output.
