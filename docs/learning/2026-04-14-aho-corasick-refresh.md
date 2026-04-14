# 2026-04-14 Aho-Corasick Refresh

## Refresher
- trie edges encode pattern prefixes
- a failure link points to the longest proper suffix that is also a trie prefix
- BFS is the clean way to build failure links because parent failure states are known first
- every input character advances, falls back through failure links, or returns to root

## Quick self-test
1. Why are suffix outputs copied through failure links? So matches like `he` still appear when `she` matches.
2. What is the main runtime after preprocessing? Linear in text length plus emitted matches.
3. Why keep line/column mapping outside the automaton state? It separates text presentation from core matching logic.
