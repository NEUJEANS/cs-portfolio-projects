# robin-hood-hashing-lab research notes

## Why this project
The repo already has cuckoo, extendible, count-min sketch, and consistent-hashing projects, but it did not yet have a clean Robin Hood hashing example. That leaves a gap in the open-addressing story for students who want to explain variance reduction, clustering, and deletion tradeoffs in a single interview-friendly artifact.

## Brief web refresh
- Robin Hood hashing is an open-addressing strategy that keeps probe lengths more even by letting entries with larger probe distance displace entries with shorter probe distance.
- Backward-shift deletion is the natural companion because it preserves probe-sequence invariants without leaving tombstones behind forever.
- A practical portfolio slice should make the invariants visible: slot/home position, probe distance, swap count, and load-factor benchmarks.

## Design choices for this slice
- Language: Python 3 standard library only
- Hashing: deterministic SHA-256-derived slot selection so tests and artifacts stay reproducible
- UX: CLI commands for build, stats, lookup, remove, export, and benchmark
- Persistence: JSON snapshots to keep the project resumable and inspectable
- Benchmark focus: average insert probes, successful lookup probes, max probe distance, and total swaps

## References
- https://en.wikipedia.org/wiki/Robin_Hood_hashing
- https://codecapsule.com/2013/11/11/robin-hood-hashing/
- https://codecapsule.com/2013/11/17/robin-hood-hashing-backward-shift-deletion/
