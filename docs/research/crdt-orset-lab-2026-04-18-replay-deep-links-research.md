# CRDT OR-Set Lab — replay deep links research (2026-04-18)

## Goal
Add static-host-friendly deep links so the replay artifact can open directly on a chosen step or sync checkpoint.

## Quick references checked
- MDN `Location.hash`
- MDN `Window: hashchange event`

## Notes pulled into the implementation
- `location.hash` is the simplest static-page state channel for a generated artifact because it works on plain file/static hosting without a server round-trip.
- `hashchange` fires when the fragment changes via navigation or link clicks, which makes it a good hook for re-rendering the replay state.
- `history.replaceState(...)` can update the canonical URL hash during slider/playback navigation without triggering another `hashchange` loop.

## Resulting product decision
- Use `#step-N` for any replay frame.
- Use `#sync-N` as the stable, demo-friendly link for sync checkpoints.
- Parse the hash on load, re-render on `hashchange`, and update the hash during normal replay navigation with `replaceState`.
