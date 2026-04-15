# Review Pass 1 - Distributed Snapshot Mermaid Export

## Focus
- generated Mermaid syntax validity
- renderer portability

## Findings
1. The first channel-state note used `Note over C->B`, which is not a valid participant target in Mermaid sequence diagrams.

## Fixes applied
- rewrote channel-state notes to target the sender and receiver participants instead
- preserved the channel name in note text so the recorded direction is still explicit
- reran project tests after the change
