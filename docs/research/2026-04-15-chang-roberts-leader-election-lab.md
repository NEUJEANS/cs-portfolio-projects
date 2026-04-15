# Chang-Roberts leader election lab research

## Goal
Add a compact but interview-strong distributed-systems project that complements the repo's existing routing, Raft, vector-clock, and Chord simulations.

## Design notes
- Prefer a small simulator with explicit traces over a large framework.
- Keep the first slice deterministic and easy to test.
- Include a leader-announcement phase so the output feels closer to a complete protocol demonstration.
- Model failures conservatively by removing failed nodes from the active ring before the run.

## Why it belongs in the portfolio
- covers classic leader election, a missing cornerstone distributed-systems topic in the current set
- produces clean JSON artifacts that can later feed visualizations
- is easy to demo live in an interview without external services
