# Learning refresh — 2026-04-19 — page replacement WSClock window

## Quick refresher
- WSClock adds a working-set age threshold `tau` on top of Clock-style hand scans.
- In this simulator, `tau` is measured in references, so a smaller window makes WSClock evict pages more aggressively.
- A larger window makes pages stay "active" longer, which tends to help on traces with recurring hot sets but can delay eviction during scans.
- The default heuristic remains `max(4, frames * 2)`, but an explicit override is useful for portfolio experiments and interview demos.

## Self-check
For the built-in `compiler-phase-shift` benchmark at 5 frames:
- `--wsclock-window 1` should produce `54` WSClock faults.
- `--wsclock-window 5` should produce `52` WSClock faults.
- the default auto heuristic should also resolve to `52` faults at 5 frames because the effective window becomes `10`.

## Why this slice matters
- it turns WSClock from a fixed black-box heuristic into a tunable experiment students can explain
- it makes the page-replacement lab better for storytelling about phase shifts, working sets, and eviction aggressiveness
- it lays groundwork for a later dirty-page-aware WSClock slice where `tau` and cleaning behavior interact more realistically
