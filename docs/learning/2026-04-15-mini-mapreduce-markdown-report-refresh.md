# Mini MapReduce Markdown report refresh

Date: 2026-04-15

## Focus
- Generate deterministic Markdown artifacts from existing benchmark JSON-like structures.
- Keep tables stable so tests can assert exact headers.
- Summarize reducer skew with small derived metrics instead of dumping raw rows only.

## Quick self-test
1. A Markdown report function should return a trailing newline so CLI file output is diff-friendly.
2. Derived stats should avoid divide-by-zero and handle single-reducer cases.
3. Visual load markers should stay deterministic for the same numeric inputs.

## Chosen approach
- Reuse the existing benchmark payload as the source of truth.
- Render one timing summary table plus one heatmap summary section per reducer count.
- Include lightweight text bars in the Markdown table cells so the artifact is useful even without external chart tooling.
