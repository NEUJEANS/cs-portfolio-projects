# Aho-Corasick Search Lab

A portfolio-friendly algorithms project that implements the Aho-Corasick multi-pattern string matching algorithm with a practical CLI.

## Features
- builds a trie with failure links for efficient multi-pattern search
- reports exact line/column offsets for every match
- supports inline text or file input
- supports case-insensitive search and JSON output for tooling
- keeps pattern counts and detailed match listings in one pass through the input text

## Why it is interesting
- demonstrates trie construction, BFS failure-link building, and suffix-output propagation
- shows how textbook string matching can become a usable developer tool
- gives interview-ready complexity discussion: `O(total_pattern_length + text_length + matches)` after preprocessing

## Usage
```bash
python3 projects/aho-corasick-search-lab/aho_corasick_search.py he she hers --text "ushers"
python3 projects/aho-corasick-search-lab/aho_corasick_search.py --pattern-file projects/aho-corasick-search-lab/sample_patterns.txt --input projects/aho-corasick-search-lab/sample_text.txt --json
python3 projects/aho-corasick-search-lab/aho_corasick_search.py alpha beta --text "Alpha beta" --ignore-case --context 4
```

## Example output
```text
patterns: 3
matches: 3
counts:
  - he: 1
  - she: 1
  - hers: 1
matches detail:
  - she @ line 1, col 2 [1:4]
  - he @ line 1, col 3 [2:4]
  - hers @ line 1, col 3 [2:6]
```

## Tests
```bash
python3 projects/aho-corasick-search-lab/test_aho_corasick_search.py
```

## Future improvements
- add streaming/chunked search for very large files while preserving boundary matches
- support whole-word mode and pattern metadata tags
- expose automaton visualization data for teaching demos
