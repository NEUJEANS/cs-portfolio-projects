# minhash-near-duplicate-lab

A portfolio-ready Python lab for finding near-duplicate text documents with shingling, exact Jaccard similarity, MinHash signatures, and LSH-style banding.

## Why it is interesting
- demonstrates a classic large-scale text-deduplication technique used in search, crawl cleanup, and plagiarism-style analysis
- lets you talk about exact similarity vs probabilistic approximation
- stays runnable locally with standard-library-only code and CLI workflows
- includes both pairwise comparison and corpus scanning modes
- now supports persisted signature indexes and benchmark runs for repeated demos

## Features
- token normalization with `word`, `code`, and `char` shingle modes
- exact Jaccard similarity for ground-truth comparisons
- deterministic MinHash signature generation with configurable signature length
- LSH-style banding to surface likely duplicate pairs without brute-force comparison of every pair
- small-corpus fallback that still checks all pairs when banding would otherwise miss every candidate in tiny demos
- persistent signature-index export for repeated scans without recomputing signatures every time
- incremental index refresh that reuses stored signatures for unchanged files based on content hashes
- dry-run refresh summaries that preview which files would be reused, updated, added, or removed before rewriting the saved index
- persisted indexes record token mode plus identifier/literal-normalization metadata so repeated scans stay compatible with the original shingling strategy
- optional identifier normalization for `code` mode so variable renames can collapse into the same near-duplicate fingerprint
- optional literal normalization for `code` mode so integer, float, string, boolean, and `None`-only edits can be grouped into stronger clone-detection demos
- benchmark mode that compares LSH candidate generation against exact all-pairs scanning
- benchmark export support for JSON, CSV, or Markdown portfolio summaries
- curated demo corpus presets for mixed Markdown/code notebooks, data-science feature pipelines, systems reconciliation stories, and web-dev component clone portfolios
- artifact-ready preset bundle export that writes JSON, Markdown, and HTML gallery cards alongside a generated preset corpus
- comma-separated glob support so one run can scan `.md`, `.py`, `.ipynb`, `.tsx`, `.ts`, and other mixed corpus files together
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

Compare two code snippets using code-token shingles instead of plain word tokenization:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare \
  samples/a.py samples/b.py \
  --token-mode code \
  --shingle-size 4 \
  --json
```

Collapse non-keyword identifiers in code mode so renamed variables/functions look more similar:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare \
  samples/a.py samples/b.py \
  --token-mode code \
  --normalize-identifiers \
  --shingle-size 3 \
  --json
```

Also collapse literals when the logic stays the same but constants, strings, or flags differ:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py compare \
  samples/a.py samples/b.py \
  --token-mode code \
  --normalize-identifiers \
  --normalize-literals \
  --shingle-size 3 \
  --json
```

Scan a corpus of `.txt` files for likely duplicates:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus \
  samples/ \
  --glob '*.txt' \
  --threshold 0.45 \
  --json
```

Generate a curated mixed-language demo corpus, then scan Markdown, Python, and notebook files together with one comma-separated glob list:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py write-preset \
  mixed-markdown-code-notebook \
  tmp/minhash-mixed-demo \
  --json

python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus \
  tmp/minhash-mixed-demo \
  --glob '*.md,*.py,*.ipynb' \
  --token-mode code \
  --normalize-identifiers \
  --normalize-literals \
  --shingle-size 4 \
  --threshold 0.2 \
  --json
```

Generate a data-science-flavored feature-engineering preset for notebook screenshots and model-pipeline clone demos:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py write-preset \
  data-science-feature-pipeline \
  tmp/minhash-data-science-demo \
  --json
```

Generate a systems-programming preset centered on replica lag / WAL reconciliation stories:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py write-preset \
  systems-churn-reconciliation \
  tmp/minhash-systems-demo \
  --json
```

Generate a frontend-focused preset with near-duplicate React dashboard cards and hooks, then scan `.tsx`, `.ts`, `.md`, and `.css` files together:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py write-preset \
  web-dev-component-clones \
  tmp/minhash-web-dev-demo \
  --json

python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus \
  tmp/minhash-web-dev-demo \
  --glob '*.tsx,*.ts,*.md,*.css' \
  --token-mode code \
  --normalize-identifiers \
  --normalize-literals \
  --shingle-size 4 \
  --threshold 0.15 \
  --json
```

Generate the same preset together with a screenshot-friendly Markdown/HTML artifact bundle:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py write-preset \
  web-dev-component-clones \
  tmp/minhash-web-dev-demo \
  --artifact-bundle-dir docs/artifacts/minhash-near-duplicate-lab/web-dev-component-clones \
  --json
```

The same `--artifact-bundle-dir` flag works with the mixed-markdown, data-science, and systems presets too, so every curated corpus can ship with portfolio-ready bundle files.

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

Preview what would change before refreshing a very large index:

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py refresh-index \
  samples/minhash-index.json \
  --dry-run \
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
  "token_mode": "word",
  "normalize_identifiers": false,
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
- why word, code-token, and character shingles each highlight different kinds of near-duplicate structure
- when identifier normalization helps code-clone detection and when it can hide semantically meaningful renames
- when literal normalization helps surface parameterized clones across integers, floats, strings, booleans, and `None`, and when it can over-merge meaningful configuration changes
- why k-shingles preserve local ordering better than simple bag-of-words counts
- how MinHash compresses large shingle sets into signatures that approximate Jaccard similarity
- why LSH banding reduces the number of candidate pairs you need to inspect exactly
- why persisted signatures matter when you rerun scans across the same corpus repeatedly
- how content hashes let incremental refresh skip unchanged documents while still keeping the index trustworthy
- why a dry-run diff is useful before reindexing a large corpus or deleting stale paths from a saved signature index
- how recall and candidate-reduction trade off as you change shingle size, signature length, and band count
- how reusable JSON/CSV/Markdown exports make experimental results easier to paste into portfolio write-ups and charts
- how preset bundle Markdown/HTML cards turn a synthetic corpus into something you can screenshot quickly for a portfolio case study

## Test

```bash
python3 -m unittest tests.test_minhash_near_duplicate
```

## Future improvements
- add richer benchmark dataset packs with expected-recall scenarios across tiny, medium, and noisy corpora
- add language-aware literal buckets for lists, dicts, template strings, and JSX-specific inline objects in code mode
- add a cross-preset landing page that compares the mixed-language, data-science, systems, and web-dev demo bundles side by side
