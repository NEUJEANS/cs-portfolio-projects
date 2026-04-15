# network-flow graphviz review pass 1

## Focus
Feature completeness and CLI ergonomics for the new DOT export slice.

## Findings
1. DOT export covered the core use case for both max-flow and matching graphs.
2. The CLI wrote DOT files successfully, but the JSON payload did not report where the artifact was saved.
3. README needed to mention the artifact path surfaced by the CLI for downstream automation.

## Fixes applied
- added `dot_output` to CLI JSON responses when `--dot-out` is used
- updated README wording to document the returned artifact path
