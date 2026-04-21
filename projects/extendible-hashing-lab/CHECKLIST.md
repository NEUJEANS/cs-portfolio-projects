# extendible-hashing-lab Checklist

- [x] do brief research on extendible hashing, directory aliasing, and global/local depth rules
- [x] refresh the split and directory-doubling model with a short self-test note before coding
- [x] add a new database-indexing portfolio lab that complements the repo's B-tree and LSM-tree projects
- [x] implement the initial extendible hash table with insert/update, lookup, delete, snapshot persistence, and CLI inspection commands
- [x] add a workload runner plus Markdown trace export for portfolio-friendly demos
- [x] add automated tests for splitting behavior, snapshot round-trips, validation failures, and CLI flows
- [x] complete at least 3 review passes and fix issues found
- [x] run tests, secret scan, commit, push, and wrap up the slice
- [x] add bucket merge / directory shrink support for delete-heavy scenarios
- [x] add benchmark comparisons against cuckoo hashing or B-tree lookup/update workloads
- [x] add HTML/SVG visualization exports for split sequences and directory aliasing
- [x] broaden the benchmark story with B-tree pages or linear probing as additional baselines
- [x] add a linear-probing baseline or compact benchmark dashboard for the artifact bundle
- [x] add a linear-probing baseline so the benchmark suite covers a simpler open-addressing comparison alongside cuckoo hashing
- [x] add a clustering-focused benchmark preset so the linear-probing baseline is even easier to demo live
- [ ] add percentile/phase-split probe summaries so successful vs unsuccessful linear-probing lookups are easier to compare in the dashboard
