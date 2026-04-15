# Review Pass 2 - Distributed Snapshot Lab

## Focus
- snapshot accounting
- consistent-cut money conservation

## Findings
1. The first version undercounted total money in the snapshot when a message on the initiator's outgoing channel should have been reflected in the receiver's recorded local state rather than channel state.

## Fixes applied
- adjusted snapshot balance computation so messages that arrive before a receiver's first marker are folded into that receiver's recorded local balance
- kept delayed incoming channels as explicit channel-state entries only when they remain open longer than the first marker window
- updated the CLI expectation to match the corrected semantics
