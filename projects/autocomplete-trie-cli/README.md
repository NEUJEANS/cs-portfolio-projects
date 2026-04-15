# autocomplete-trie-cli

## Overview
A weighted trie autocomplete command-line tool that supports both exact prefix suggestions and typo-tolerant fuzzy matches.

This is a portfolio-friendly CS project because it combines a classic prefix tree with ranked retrieval, bounded edit-distance search, and a lightweight benchmark mode in a compact, demoable program.

## Stack
- Python 3
- standard library only

## Features
- loads `word,weight` entries from a simple CSV-like text file
- returns top-k weighted exact prefix matches
- falls back to bounded fuzzy suggestions for typo-prone queries
- sorts fuzzy results by lower edit distance first, then higher weight
- supports one-shot human-readable output or machine-readable JSON
- includes batch benchmark mode for repeated queries and timing summaries
- adds optional `--explain` diagnostics so you can show trie traversal, pruning, and dynamic-programming work during demos
- includes a sample dataset and unit tests

## Usage
Single query mode:
```bash
python3 autocomplete.py sample_words.csv app
python3 autocomplete.py sample_words.csv aple --limit 3 --max-distance 1
python3 autocomplete.py sample_words.csv app --json
python3 autocomplete.py sample_words.csv aple --limit 3 --max-distance 1 --explain
```

Batch benchmark mode:
```bash
cat > sample_queries.txt <<'EOF'
app
aple
banan
EOF

python3 autocomplete.py sample_words.csv --batch-file sample_queries.txt
python3 autocomplete.py sample_words.csv --batch-file sample_queries.txt --json
python3 autocomplete.py sample_words.csv --batch-file sample_queries.txt --explain
```

Example output:
```text
query: aple
exact_prefix_matches:
- none

fuzzy_matches:
- apple (distance=1, weight=100)
- apply (distance=1, weight=87)

prefix_time_ms: 0.012
fuzzy_time_ms: 0.046
```

Benchmark summary example:
```text
benchmark_summary:
- queries: 3
- indexed_words: 8
- avg_prefix_time_ms: 0.009
- avg_fuzzy_time_ms: 0.041
- slowest_prefix_query: app (0.014 ms)
- slowest_fuzzy_query: banan (0.057 ms)

per_query_top_hits:
- app: prefix=[apple, application, apply] fuzzy=[none] prefix_ms=0.014 fuzzy_ms=0.029
```

Explain-mode excerpt:
```text
search_explanation:
- prefix_search:
  - nodes_visited: 4
  - terminal_words_considered: 3
  - heap_updates: 3
  - branches_pruned_by_weight: 1
- fuzzy_search:
  - trie_edges_evaluated: 11
  - dynamic_programming_rows: 11
  - terminal_words_considered: 4
  - accepted_matches_within_distance: 2
  - branches_pruned_by_distance: 3
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is a good CS portfolio project
- demonstrates trie-based indexing and prefix traversal
- shows practical ranking logic instead of plain alphabetical output
- adds typo handling with dynamic-programming-based edit distance search
- includes timing instrumentation and batch benchmarking for performance discussion
- exposes explain-mode diagnostics that make trie pruning and DP-based fuzzy matching easier to discuss in interviews
- is easy to extend into a service, web UI, or larger search system

## Future Improvements
- cache hot query prefixes for lower repeated-query latency
- support phrase suggestions and token-level autocomplete
- add larger synthetic datasets and comparison baselines
- expose the engine as a tiny HTTP API for frontend demos
