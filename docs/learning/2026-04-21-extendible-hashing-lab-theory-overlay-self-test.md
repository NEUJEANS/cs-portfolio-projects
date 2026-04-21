# extendible-hashing-lab theory-overlay self-test — 2026-04-21

## Quick refresh
- linear probing performance is usually explained with probe-count expectations as a function of load factor `α`
- successful searches map best to lookup hits (and deletes after the key is found), while unsuccessful searches map best to lookup misses and insert-style scans
- observed workload costs can exceed the compact formulas when clustering and tombstones distort the probe distribution, so the overlay should emphasize comparison rather than exact prediction
- resumable portfolio artifacts should keep the same theory fields visible in JSON, Markdown, HTML, and CSV outputs

## Self-test
1. **Q:** Why use occupied load factor for the theory overlay instead of only final live-entry load factor?
   **A:** Because tombstones still lengthen probe chains, so occupied load factor better reflects the pressure the linear table experiences during the benchmark.
2. **Q:** What are the two formulas worth exposing in the artifact bundle?
   **A:** `successful ≈ 0.5 * (1 + 1 / (1 - α))` and `unsuccessful ≈ 0.5 * (1 + 1 / (1 - α)^2)`.
3. **Q:** What should a recruiter be able to infer from the overlay in the clustering scenario?
   **A:** That miss probes spike above the compact expectation because clustering/tombstones make the simple baseline pay extra cost compared with the cleaner average-case model.
