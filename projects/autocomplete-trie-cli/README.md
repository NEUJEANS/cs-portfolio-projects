# autocomplete-trie-cli

## Overview
A weighted trie autocomplete command-line tool that supports both exact prefix suggestions and typo-tolerant fuzzy matches.

This is a portfolio-friendly CS project because it combines a classic prefix tree with ranked retrieval and bounded edit-distance search in a compact, demoable program.

## Stack
- Python 3
- standard library only

## Features
- loads `word,weight` entries from a simple CSV-like text file
- returns top-k weighted exact prefix matches
- falls back to bounded fuzzy suggestions for typo-prone queries
- sorts fuzzy results by lower edit distance first, then higher weight
- includes a sample dataset and unit tests

## Usage
```bash
python3 autocomplete.py sample_words.csv app
python3 autocomplete.py sample_words.csv aple --limit 3 --max-distance 1
```

Example output:
```text
exact_prefix_matches:
- none

fuzzy_matches:
- apple (distance=1, weight=100)
- apply (distance=1, weight=87)
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is a good CS portfolio project
- demonstrates trie-based indexing and prefix traversal
- shows practical ranking logic instead of plain alphabetical output
- adds typo handling with dynamic-programming-based edit distance search
- is easy to extend into a service, web UI, or larger search system

## Future Improvements
- cache hot query prefixes for lower repeated-query latency
- support phrase suggestions and token-level autocomplete
- add benchmark mode for large synthetic dictionaries
- expose the engine as a tiny HTTP API for frontend demos
