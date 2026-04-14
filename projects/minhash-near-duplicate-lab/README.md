# minhash-near-duplicate-lab

A portfolio-ready Python lab for finding near-duplicate text documents with shingling, exact Jaccard similarity, MinHash signatures, and LSH-style banding.

## Why it is interesting
- demonstrates a classic large-scale text-deduplication technique used in search, crawl cleanup, and plagiarism-style analysis
- lets you talk about exact similarity vs probabilistic approximation
- stays runnable locally with standard-library-only code and CLI workflows
- includes both pairwise comparison and corpus scanning modes

## Features
- token normalization and word-shingle generation
- exact Jaccard similarity for ground-truth comparisons
- deterministic MinHash signature generation with configurable signature length
- LSH-style banding to surface likely duplicate pairs without brute-force comparison of every pair
- small-corpus fallback that still checks all pairs when banding would otherwise miss every candidate in tiny demos
- CLI output in human-readable or JSON form
- repository-level tests for API behavior and CLI workflows

## Usage

Compare two files directly:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare \
  samples/a.txt samples/b.txt \
  --shingle-size 3 \
  --num-hashes 64 \
  --bands 8
```

Scan a corpus of `.txt` files for likely duplicates:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus \
  samples/ \
  --glob '*.txt' \
  --threshold 0.45 \
  --json
```

## Example JSON output

```json
{
  "bands": 8,
  "command": "compare",
  "estimated_jaccard": 0.5781,
  "exact_jaccard": 0.6,
  "left": "samples/a.txt",
  "left_shingles": 8,
  "right": "samples/b.txt",
  "right_shingles": 9,
  "shared_bands": 2
}
```

## Interview talking points
- why k-shingles preserve local ordering better than simple bag-of-words counts
- how MinHash compresses large shingle sets into signatures that approximate Jaccard similarity
- why LSH banding reduces the number of candidate pairs you need to inspect exactly
- how false positives and false negatives shift as you change shingle size, signature length, and band count

## Test

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Future improvements
- add character-shingle and code-token modes for source-code deduplication demos
- persist signatures to disk for repeated corpus scans on larger datasets
- benchmark approximate candidate generation vs naive all-pairs comparison
