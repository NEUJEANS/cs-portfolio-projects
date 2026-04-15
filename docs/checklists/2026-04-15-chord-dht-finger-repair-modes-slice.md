# Chord DHT finger-repair modes slice

- Timestamp: 2026-04-15 11:49 UTC
- Project: `projects/chord-dht-lab`
- Goal: make stabilization more realistic by modeling alternative `fix_fingers` scheduling strategies.

## Plan
- [x] sync repo before editing
- [x] inspect current stabilization/reporting gaps
- [x] skip web research because this is a direct extension of the existing Chord simulator
- [x] do a short Python state-update/randomness self-check
- [x] implement configurable finger repair modes: `single`, `all`, `random`
- [x] expose the controls in CLI and Graphviz stabilization export
- [x] add/update tests for scheduling determinism and CLI behavior
- [x] run tests
- [x] review pass 1
- [x] review pass 2
- [x] review pass 3
- [x] secret scan
- [ ] commit, push, wrap-up

## Notes
- `random` mode must stay reproducible, so it requires a seed.
- Keep the slice resumable by recording repaired finger slots in each round payload.
