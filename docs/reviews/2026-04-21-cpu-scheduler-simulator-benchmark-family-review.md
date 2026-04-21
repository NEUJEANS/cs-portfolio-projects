# CPU scheduler benchmark family review log

## Pass 1, benchmark ranking audit
- Issue found: the first benchmark scoreboard used raw total win counts, which overstated tie-heavy metrics like throughput and completion time and made the pack ranking look more decisive than it really was.
- Fix: add tie-aware fractional `score_points` and use that in the aggregate scoreboard while keeping raw win counts in a separate table.

## Pass 2, scenario roster readability audit
- Issue found: the benchmark roster only showed scenario names and sources, so generated workloads were harder to interpret without opening each nested artifact.
- Fix: add a description column to the Markdown and HTML roster tables.

## Pass 3, CLI ergonomics audit
- Issue found: `--help` still described `--algorithms` as compare-only and the positional workload help did not clearly explain benchmark mode.
- Fix: refresh the parser help text so benchmark mode is described accurately.
