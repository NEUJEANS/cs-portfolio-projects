# minhash-near-duplicate-lab

A portfolio-ready Python lab for finding near-duplicate text documents with shingling, exact Jaccard similarity, MinHash signatures, and LSH-style banding.

## Why it is interesting
- demonstrates a classic large-scale text-deduplication technique used in search, crawl cleanup, and plagiarism-style analysis
- lets you talk about exact similarity vs probabilistic approximation
- stays runnable locally with standard-library-only code and CLI workflows
- includes both pairwise comparison and corpus scanning modes
- now supports persisted signature indexes and benchmark runs for repeated demos

## Features
- token normalization and word-shingle generation
- exact Jaccard similarity for ground-truth comparisons
- deterministic MinHash signature generation with configurable signature length
- LSH-style banding to surface likely duplicate pairs without brute-force comparison of every pair
- small-corpus fallback that still checks all pairs when banding would otherwise miss every candidate in tiny demos
- persistent signature-index export for repeated scans without recomputing signatures every time
- incremental index refresh that reuses stored signatures for unchanged files based on content hashes
- benchmark mode that compares LSH candidate generation against exact all-pairs scanning
- benchmark export support for JSON, CSV, or Markdown portfolio summaries
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

Build a persistent signature index:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py build-index \
  samples/ \
  samples/minhash-index.json \
  --glob '*.txt' \
  --json
```

Scan using a previously saved index:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py scan-index \
  samples/minhash-index.json \
  --threshold 0.45 \
  --json
```

Refresh an existing index after some files changed:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py refresh-index \
  samples/minhash-index.json \
  --json
```

Benchmark candidate reduction vs exact all-pairs scanning:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark \
  samples/ \
  --glob '*.txt' \
  --threshold 0.45 \
  --json
```

Save the benchmark summary for a README, blog post, or spreadsheet:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark \
  samples/ \
  --glob '*.txt' \
  --threshold 0.45 \
  --output docs/minhash-benchmark-summary.md \
  --json
```

## Example JSON output

```json
{
  "command": "benchmark",
  "documents_scanned": 12,
  "all_pairs": 66,
  "candidate_pairs": 9,
  "exact_pairs_above_threshold": 4,
  "lsh_pairs_above_threshold": 4,
  "lsh_recall_vs_exact": 1.0,
  "candidate_reduction_ratio": 0.8636,
  "timings_seconds": {
    "build_signatures": 0.004821,
    "lsh_candidate_generation": 0.000517,
    "exact_all_pairs_scan": 0.001933
  }
}
```

## Interview talking points
- why k-shingles preserve local ordering better than simple bag-of-words counts
- how MinHash compresses large shingle sets into signatures that approximate Jaccard similarity
- why LSH banding reduces the number of candidate pairs you need to inspect exactly
- why persisted signatures matter when you rerun scans across the same corpus repeatedly
- how content hashes let incremental refresh skip unchanged documents while still keeping the index trustworthy
- how recall and candidate-reduction trade off as you change shingle size, signature length, and band count
- how reusable JSON/CSV/Markdown exports make experimental results easier to paste into portfolio write-ups and charts

## Test

```bash
python3 -m unittest tests.test_minhash_near_duplicate
```

## Future improvements
- add character-shingle and code-token modes for source-code deduplication demos
- add a dry-run corpus diff summary before refresh for very large indexes
