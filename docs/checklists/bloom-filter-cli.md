# bloom-filter-cli checklist

- [x] choose project scope and document Bloom filter formulas
- [x] implement BloomFilter core with calculated parameters
- [x] support add/check/bulk operations
- [x] support JSON save/load for resumable use
- [x] expose a CLI with build/check/stats subcommands
- [x] add tests for math, membership, serialization, and CLI flows
- [x] log three review passes and fix issues found
- [x] prepare wrap-up with next step
- [x] add optional benchmark mode for observed false-positive sampling on generated tokens

## Next ideas
- [ ] add counting Bloom filter variant for delete support
- [ ] add binary export format for larger filters
