# Union-Find comparison Markdown summary refresh

## Refresher
- Markdown export should lead with the result, not the implementation details.
- For portfolio snippets, the strongest structure is: headline numbers, why-it-matters paragraph, compact metric bullets, one interview-ready takeaway.
- Reproducible artifacts are more credible when the summary is generated directly from the JSON comparison payload instead of hand-written prose.

## Self-test
1. Which metrics should be surfaced first from a connectivity comparison artifact?
   - elapsed time, throughput, speedup, and parity/correctness checks.
2. Why generate Markdown from the artifact instead of maintaining a separate note manually?
   - it avoids drift and makes README/blog snippets refreshable after each benchmark run.
3. What should a portfolio summary avoid?
   - giant raw JSON dumps, implementation trivia before outcomes, and claims without the benchmark numbers.
