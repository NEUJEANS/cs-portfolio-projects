# Task Tracker CLI Research Notes — 2026-04-14

A small task tracker is a strong portfolio starter because it shows end-to-end thinking without heavy setup:
- command-line UX
- local persistence
- data modeling
- filtering/reporting
- testing discipline

Good portfolio framing:
- keep the feature set focused but polished
- separate domain logic from CLI glue
- document trade-offs and next steps
- include tests that prove behavior, not just smoke-test the script

Implementation choice for this slice:
- Python + standard library only
- JSON persistence for zero-dependency local runs
- atomic save via temp file replacement
- service layer for easier future expansion
