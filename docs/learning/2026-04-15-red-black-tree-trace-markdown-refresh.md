# Red-Black Tree Trace Markdown Refresh — 2026-04-15

## Quick refresh used for this slice
- Existing trace events are more stable than trying to infer balancing logic from the final tree state after the fact.
- A portfolio artifact is stronger when the CLI can emit Markdown directly instead of requiring manual README rewriting.
- For small CLIs, adding one focused export command is usually cleaner than overloading JSON-only commands with presentation flags.

## Self-test
1. Why base the explainer on trace events instead of replaying the final tree structure?
   - The trace preserves the actual balancing path, including recolors and intermediate rotations that disappear in the final shape.
2. Why keep the Markdown export as a separate command?
   - It avoids breaking the existing JSON contracts for `build`, `delete`, and `demo`, while giving portfolio users a presentation-oriented output path.
3. Why test file output instead of only returned strings?
   - The real portfolio workflow is generating an artifact someone can commit, render, or link from a README.
