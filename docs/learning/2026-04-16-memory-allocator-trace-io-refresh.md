# memory-allocator trace I/O refresh

## Refresher
- replayable CLI traces are easiest to keep stable as JSON objects with explicit `operations` plus optional config defaults
- letting CLI flags override trace defaults keeps batch reruns resumable without editing the saved trace file
- exporting the resolved config makes a trace self-contained for later demos, regression cases, or interview walkthroughs

## Self-test
- confirmed a trace file can provide `capacity`, `strategy`, `alignment`, `timeline`, and `timeline_width`
- confirmed `--trace-out` writes a replayable JSON bundle after a normal CLI run
- confirmed imported trace operations still flow through the existing operation executor and timeline capture
