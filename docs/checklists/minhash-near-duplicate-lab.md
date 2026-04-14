# minhash-near-duplicate-lab checklist

## Initial slice (2026-04-14 21:19 UTC run)
- [x] confirm repo sync before editing
- [x] do brief research on shingling, MinHash, Jaccard similarity, and banding
- [x] refresh Python standard-library implementation patterns and self-test the planned API shape
- [x] create a new portfolio-worthy project for near-duplicate text detection
- [x] implement exact comparison plus approximate MinHash/LSH-style corpus scanning
- [x] add README usage, interview talking points, and future improvements
- [x] add repository-level automated tests for API behavior and CLI flows
- [x] complete at least 3 review passes and log fixes

## Persistence + benchmark slice (2026-04-14 22:33 UTC run)
- [x] confirm repo sync before editing
- [x] review prior roadmap and choose the unfinished persistence/benchmark follow-up
- [x] do a quick Python refresh/self-test against the current MinHash API before editing
- [x] add persistent signature index support with metadata and reusable stored signatures
- [x] add CLI commands for `build-index` and `scan-index`
- [x] add a benchmark command comparing LSH candidate generation with exact all-pairs scanning
- [x] expand tests for index round-trips and new CLI flows
- [x] update README with new usage examples and interview talking points
- [x] complete at least 3 review passes and fix issues found
- [ ] future slice: incremental index refresh for unchanged files and richer benchmark exports
