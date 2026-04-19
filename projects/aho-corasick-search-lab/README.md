# Aho-Corasick Search Lab

A portfolio-friendly algorithms project that implements the Aho-Corasick multi-pattern string matching algorithm with a practical CLI.

## Features
- builds a trie with failure links for efficient multi-pattern search
- reports exact line/column offsets for every match
- supports inline text or file input
- supports case-insensitive search and JSON output for tooling
- keeps pattern counts and detailed match listings in one pass through the input text
- supports chunked file scanning so large inputs can be streamed without losing matches that cross chunk boundaries
- supports sampled context windows in chunked mode so streamed searches can still show small excerpts without loading the entire file

## Why it is interesting
- demonstrates trie construction, BFS failure-link building, and suffix-output propagation
- shows how textbook string matching can become a usable developer tool
- adds a practical streaming mode that carries automaton state across chunk boundaries instead of re-reading overlap windows by hand
- shows how to layer small UX features like context windows onto a streaming pipeline with bounded memory
- gives interview-ready complexity discussion: `O(total_pattern_length + text_length + matches)` after preprocessing

## Usage
```bash
python3 projects/aho-corasick-search-lab/aho_corasick_search.py he she hers --text "ushers"
python3 projects/aho-corasick-search-lab/aho_corasick_search.py --pattern-file projects/aho-corasick-search-lab/sample_patterns.txt --input projects/aho-corasick-search-lab/sample_text.txt --json
python3 projects/aho-corasick-search-lab/aho_corasick_search.py alpha beta --text "Alpha beta" --ignore-case --context 4
python3 projects/aho-corasick-search-lab/aho_corasick_search.py warning critical --input logs/app.log --chunk-size 4096 --context 12
python3 projects/aho-corasick-search-lab/aho_corasick_search.py warning critical --input logs/app.log --chunk-size 4096 --context 12 --json
```

## Example output
```text
patterns: 2
matches: 2
input mode: stream (4 chunks @ 5 chars, boundary overlap 7)
context chars: 2 (sampled around matches)
counts:
  - warning: 1
  - critical: 1
matches detail:
  - warning @ line 2, col 1 [6:13] | context='r\n⟦warning⟧\nc'
  - critical @ line 3, col 1 [14:22] | context='g\n⟦critical⟧\n'
```

## Streaming notes
- `--chunk-size` only applies to `--input` mode
- chunked mode preserves cross-boundary matches by carrying the automaton state across chunks
- `--context` now works in both memory and chunked modes
- in chunked mode, context is emitted as a sampled window around each match instead of requiring the full file contents in memory
- JSON output includes `input.mode`, `input.chunk_count`, `input.chunk_size`, `input.boundary_overlap`, and optional per-match `context` payloads when `--context` is requested

## Tests
```bash
python3 projects/aho-corasick-search-lab/test_aho_corasick_search.py
python3 -m unittest tests.test_aho_corasick_search_lab
```

## Future improvements
- support whole-word mode and pattern metadata tags
- expose automaton visualization data for teaching demos
- export sampled contexts into a small HTML or Markdown report for portfolio screenshots
