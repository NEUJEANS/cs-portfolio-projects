# suffix-array-search-lab

A portfolio-friendly Python project that builds a suffix-array index for a text corpus and supports fast substring lookup with keyword-in-context output.

## Why it is interesting
- demonstrates a classic text-indexing data structure instead of standard CRUD work
- shows lexicographic ordering, binary search over suffixes, and line-offset lookup
- produces a reusable JSON index artifact for resumable search demos
- exposes an end-user CLI with context windows that make the algorithm easy to show in interviews

## Features
- build a suffix-array index from any UTF-8 text file
- save/load the index as JSON
- search for all substring matches using lower/upper-bound binary search
- print keyword-in-context snippets with optional line numbers and match highlighting
- support case-insensitive search for more practical demos
- inspect basic index stats

## Usage

Build an index:

```bash
python3 suffix_array_search.py build \
  --input sample_text.txt \
  --output sample_index.json
```

Search for a substring with line numbers:

```bash
python3 suffix_array_search.py search \
  --index sample_index.json \
  --show-line-numbers \
  banana
```

Case-insensitive search with narrower context:

```bash
python3 suffix_array_search.py search \
  --index sample_index.json \
  --ignore-case \
  --context 15 \
  --limit 3 \
  array
```

Inspect index metadata:

```bash
python3 suffix_array_search.py stats --index sample_index.json
```

## Test

```bash
python3 -m unittest projects/suffix-array-search-lab/test_suffix_array_search.py
```

## Future improvements
- add LCP-array acceleration for larger corpora
- support indexing multiple files with document boundaries and file-aware search output
- add benchmark scripts comparing naive scan vs. suffix-array lookup on larger texts
