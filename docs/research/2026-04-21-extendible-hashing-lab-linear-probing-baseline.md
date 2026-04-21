# Extendible hashing linear-probing baseline research — 2026-04-21

## Sources checked
- Princeton Algorithms, `Hash Tables` — https://algs4.cs.princeton.edu/34hash/
- Wikipedia, `Open addressing` — https://en.wikipedia.org/wiki/Open_addressing
- repo-local reference: `projects/robin-hood-hashing-lab/README.md`

## Notes that mattered for this slice
- Linear probing is a strong teaching baseline because it is the simplest open-addressing design to explain: collisions walk forward one slot at a time.
- The payoff is cache-friendly locality, but the cost is sensitivity to clustering; that makes it a useful contrast with extendible hashing's split-driven growth and cuckoo hashing's displacement/rehash behavior.
- Tombstones matter for delete-heavy workloads: without rebuild/cleanup pressure, probe chains can stay longer even after live entry counts drop.
- For this portfolio repo, the most honest comparison story is not “who wins overall,” but “what cost each design pays”: extendible hashing pays with directory depth/splits, linear probing pays with probe length/tombstone cleanup, cuckoo hashing pays with displacements/rehashes, and the B-tree baseline pays with paged index height/nodes/bytes.

## Takeaway for implementation
Make the linear baseline explicit in the suite config, expose its probe/tombstone/rebuild metrics in every exported artifact, and keep the README/dashboard copy clear that it is the simple open-addressing contrast alongside cuckoo hashing rather than a replacement for the extendible-hashing story.
