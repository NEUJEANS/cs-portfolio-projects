# Review pass 3 — graph-routing Mermaid slice

## Focus
Test/doc alignment review.

## Issues found
1. The new export flow was initially under-tested.
2. Negative-cycle edge assertions needed to match the actual fixture weights.

## Fixes applied
- Added tests for shortest-path reconstruction, direct Mermaid export, and CLI-driven Mermaid export.
- Corrected the negative-cycle Mermaid assertion to match the sample graph edge weight.
