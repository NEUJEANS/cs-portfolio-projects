# Aho-Corasick Search Lab Research

## Goal
Add a fresh algorithms-heavy project now that the existing portfolio set is broadly complete.

## Why this project
- strong CS signal: trie construction + BFS failure links + suffix match propagation
- practical output: search many patterns through text/logs in one pass
- interview friendly: easy to explain preprocessing cost versus query-time throughput
- complementary to existing repo projects: not another key-value store, cache, or graph traversal lab

## Notes used for this slice
- use a rooted trie where each node stores transitions, a failure link, and output patterns
- compute failure links with breadth-first traversal from depth 1 nodes
- when following a failure link, inherit output patterns so suffix matches are emitted correctly
- convert offsets to line/column for portfolio-grade usability rather than raw index-only matches
