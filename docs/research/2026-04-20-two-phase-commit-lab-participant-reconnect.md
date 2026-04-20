# Two-phase commit lab participant reconnect note — 2026-04-20

## Research decision
No extra external web research was needed for this slice.

## Why
- the new behavior is a direct extension of the already-modeled prepared-state and durable-decision rules from the initial 2PC slice
- the portfolio value here is clarifying a participant-side operational case that naturally follows from plain 2PC: a prepared node can miss the first second-phase message and stay in doubt until it reconnects
- the main design work is repo-local: keep the simulation deterministic, make the reconnect path explicit in the trace, and surface the nuance in committed Markdown artifacts

## Design takeaway
- model the missed second-phase message at the participant level instead of inventing a second coordinator failure mode
- preserve the global decision semantics (`commit` or `abort`) while still showing participant-level uncertainty and reconnect recovery in the report
- expose reconnect recovery in the catalog so the slice is visible from GitHub without opening the source first
