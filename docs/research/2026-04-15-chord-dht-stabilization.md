# Chord DHT stabilization slice research

Date: 2026-04-15
Project: `chord-dht-lab`

## Why this slice
The lab already covered routing, joins, and failover, but it still skipped one of the most interviewable Chord ideas: how nodes repair stale successor/predecessor and finger metadata after topology changes.

## Short research summary
- Chord maintenance is usually explained with repeated `stabilize`, `notify`, and `fix_fingers` style background work.
- The easiest educational simulation is to model stale metadata immediately after a join/failure, then show convergence over explicit rounds.
- For a portfolio lab, it is more useful to expose convergence progress than to build a fully asynchronous protocol emulator.

## Implementation choice
Use a deterministic round-based repair model:
1. start from stale node metadata
2. repair successor + predecessor every round
3. repair one finger slot per round
4. report per-node and aggregate convergence metrics

That keeps the lab interview-friendly while still teaching why Chord needs maintenance after membership changes.
