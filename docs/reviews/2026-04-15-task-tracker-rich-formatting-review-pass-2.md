# Review pass 2 — task tracker rich terminal formatting

- Ran a manual CLI smoke test with a temporary data file.
- Verified the new list table shows state/priority emphasis and the summary view renders the new dashboard layout in no-color mode.
- Caught one operator mistake during manual invocation (`--color` must be provided before the subcommand because it is a global flag); no code change needed because README examples already use the correct ordering.
