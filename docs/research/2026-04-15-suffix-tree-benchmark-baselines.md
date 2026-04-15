# Research Note — 2026-04-15 — Suffix Tree Benchmark Baselines

## Question
What baseline searches make sense for an educational suffix-tree lab benchmark?

## Brief findings
- Suffix trees are attractive because query traversal is linear in pattern length after preprocessing.
- Suffix arrays are usually more space-efficient in practice, but they add implementation overhead if the current project goal is a readable suffix-tree lab rather than a second indexing structure.
- For a compact portfolio slice, comparing against built-in string search and regex lookahead gives a practical baseline with low code overhead and easy reproducibility.

## Decision for this slice
Use these benchmark methods:
1. `suffix_tree.find` — the project data-structure path
2. Python `str.find` loop — simple standard-library baseline
3. regex lookahead — overlapping match baseline that still feels realistic for interview discussion

## Why not implement suffix arrays in this same slice?
That would be valuable, but it is big enough to deserve its own focused vertical slice. The current slice aims to strengthen the existing project with measurable performance artifacts without diluting the suffix-tree story.

## Sources consulted
- Cornell lecture notes on suffix trees / arrays
- Princeton Algorithms notes on suffix arrays
- high-level comparison summaries surfaced via web search for suffix tree vs suffix array exact substring search
