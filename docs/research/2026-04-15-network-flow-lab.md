# 2026-04-15 network-flow-lab research

## Why this slice
The existing repo already covered many data structures and systems labs, so the next high-signal addition should strengthen classic graph-algorithm coverage with a project that is easy to demo and discuss in interviews.

## Chosen angle
- build a compact max-flow solver rather than another CRUD-style app
- keep the implementation dependency-free and explainable
- expose augmenting paths and min cut so the output teaches the algorithm, not just the answer

## Scope for this run
- initial complete vertical slice using Edmonds-Karp
- JSON graph input and CLI output
- sample scenario + correctness tests
- leave matching/visualization as future follow-up work
