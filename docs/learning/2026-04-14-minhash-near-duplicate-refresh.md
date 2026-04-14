# Learning refresh — minhash-near-duplicate-lab

## Refresh points
- Python `dataclass` is enough for structured similarity reports without adding dependencies
- `hashlib.sha256` can produce stable per-shingle hash values for deterministic MinHash coordinates
- `itertools.combinations` is a clean fit for generating bucket-local candidate pairs
- repo-level `unittest` files can import hyphenated project directories using `importlib.util.spec_from_file_location`

## Self-test
1. Why not compare bag-of-words counts directly?
   - Because shingling preserves local adjacency, which is better for near-duplicate detection than plain token frequency alone.
2. What must hold for banding to work cleanly?
   - Signature length must be divisible by the number of bands so each band has the same row count.
3. Why keep exact Jaccard in the project if MinHash is faster?
   - Exact Jaccard provides the truth baseline and helps explain approximation error during demos and interviews.
