# Distance vector routing diagram export review log

## Review pass 1
Issue found: route snapshots needed to distinguish unreachable destinations clearly instead of implying a next hop exists.
Fix: route export labels now render `unreachable` when `next_hop` is `None`.

## Review pass 2
Issue found: multi-router route exports could become noisy for quick demos.
Fix: added `--router` to limit route snapshots to a single router for focused explanations.

## Review pass 3
Issue found: a diagram feature without README examples would weaken portfolio usability.
Fix: documented Mermaid and DOT export examples in the project README and covered the CLI path with tests.
