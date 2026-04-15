# 2026-04-15 suffix-tree-lab refresh

## Focus
- compressed suffix tree structure: edges store string spans instead of single characters
- naive educational construction is acceptable for a portfolio lab if the README is explicit about complexity tradeoffs
- useful interview-friendly operations: substring existence, occurrence reporting, longest repeated substring, and search trace explainability

## Quick self-test
1. Why append a sentinel? To ensure every suffix terminates at a unique leaf.
2. Why compress trie edges? To reduce memory overhead and make traversals reflect maximal shared substrings.
3. Why keep suffix starts below internal nodes? So matched patterns can report all occurrence offsets without rebuilding paths.
