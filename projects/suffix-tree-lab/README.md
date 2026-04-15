# suffix-tree-lab

## Overview
Build and query a compressed suffix tree for fast substring search, repeated-substring analysis, and interview-friendly structure visualization.

## Why it is portfolio-worthy
This project demonstrates string indexing, edge splitting, compact tree representations, query tracing, and testable CLI design. It is a strong discussion piece for algorithms, text search, and data-structure tradeoffs because the implementation is intentionally educational: construction is naive but the search surface behaves like a real suffix-tree interface.

## Features
- builds a compact edge-labeled suffix tree by inserting every suffix
- supports substring existence checks and occurrence lookup
- computes the longest repeated substring with configurable minimum occurrence count
- provides an `explain` mode that traces how a pattern is matched through compressed edges
- exports Graphviz DOT for quick rendering into SVG/PNG diagrams
- optionally annotates exported nodes with suffix-start offsets for debugging and demos
- includes a simple CLI for search, repetition analysis, and structure export

## CLI usage
```bash
python3 suffix_tree_lab.py banana find ana
python3 suffix_tree_lab.py banana repeat
python3 suffix_tree_lab.py mississippi repeat --min-occurrences 3
python3 suffix_tree_lab.py banana explain band
python3 suffix_tree_lab.py banana export-dot > banana.dot
dot -Tsvg banana.dot -o banana.svg
python3 suffix_tree_lab.py banana export-dot --show-suffix-starts
```

## Example output
```text
$ python3 suffix_tree_lab.py banana find ana
matches=[1, 3]

$ python3 suffix_tree_lab.py banana repeat
ana
```

```dot
$ python3 suffix_tree_lab.py banana export-dot
digraph suffix_tree {
  rankdir=LR;
  node [shape=circle, fontname="Helvetica"];
  edge [fontname="Helvetica"];
  n0 [label="root", shape=circle];
  n0 -> n1 [label="$"];
  ...
}
```

## Testing
```bash
pytest -q test_suffix_tree_lab.py
```

## Implementation notes
- appends a unique sentinel so every suffix ends at a leaf
- compresses shared prefixes into labeled edges instead of one-character trie edges
- stores suffix start offsets below each node to support occurrence reporting
- uses DOT as a zero-dependency interchange format so diagrams can be rendered externally with Graphviz
- favors readability and correctness over Ukkonen-level linear-time construction complexity

## Future improvements
- generalized suffix tree support for longest common substring across multiple texts
- richer export options such as Mermaid output or rendered artifact generation during benchmarks
- optional benchmarking against suffix arrays and regex-based search baselines
- a streaming input mode that persists the index to disk for larger corpora
