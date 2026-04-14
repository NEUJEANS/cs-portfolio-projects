# PageRank Lab Research

## Goal
Add a graph-algorithms project that is easy to demo locally but still ties directly to real search and ranking systems.

## Notes from brief research
- PageRank models a random surfer over a directed graph and iteratively updates node scores.
- A damping factor around `0.85` is the conventional default because it balances link-following and random teleportation.
- Dangling nodes (nodes with no outgoing edges) should redistribute their rank mass across the whole graph instead of trapping it.
- Good teaching/demo features for a portfolio project: edge-list input, deterministic top-k output, convergence reporting, and tests for rank normalization plus dangling-node handling.

## Slice choice
Build a pure-Python CLI that:
1. reads a local edge list,
2. computes PageRank with configurable damping/iterations/tolerance,
3. reports top-ranked nodes,
4. explains convergence metrics in JSON output.

## Why this is portfolio-worthy
- demonstrates graph modeling, iterative numerical methods, and CLI design
- gives clear interview talking points around ranking systems and probability mass conservation
- stays dependency-light and easy to run in a recruiter or class environment
