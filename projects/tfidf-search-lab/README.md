# tfidf-search-lab

## Overview
A small document-search CLI that builds an inverted index over local text files and ranks results with TF-IDF plus cosine similarity.

This is a strong CS portfolio project because it turns classic information-retrieval ideas into a runnable, explainable program instead of a toy data-structure snippet.

## Stack
- Python 3
- standard library only

## Features
- recursively indexes `.txt` and `.md` files inside a corpus directory
- tokenizes text, filters common stopwords, and computes smoothed TF-IDF weights
- uses an inverted index for candidate generation and cosine similarity for ranking
- prints score explanations with matched terms and per-term contributions
- supports plain-text and JSON output modes

## Usage
```bash
python3 tfidf_search.py sample_corpus "search ranking"
python3 tfidf_search.py sample_corpus "write ahead log durability" --stats
python3 tfidf_search.py sample_corpus "pagerank graph" --json
```

Example output:
```text
documents=3 terms=26 postings=26
search.txt | score=0.5427 | terms=[search] | contributions=[search=0.1620]
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Why it is a good CS portfolio project
- demonstrates inverted indexes, sparse vector weighting, and cosine similarity
- gives interview-friendly score explanations instead of opaque ranking output
- stays fully local and dependency-free, so reviewers can run it instantly
- leaves room for extensions into BM25, snippets, persistence, or an HTTP API

## Future Improvements
- persist index metadata for faster repeated searches
- add BM25 as a second ranking strategy
- support phrase queries and boolean operators
- generate text snippets with highlighted query terms
