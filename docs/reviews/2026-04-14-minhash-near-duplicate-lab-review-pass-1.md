# Review pass 1 — minhash-near-duplicate-lab

## Focus
- correctness of candidate generation on very small corpora

## Issue found
- pure band-collision candidate generation could return zero pairs for tiny corpora even when two documents were clearly similar enough by exact Jaccard

## Fix applied
- added a small-corpus fallback: if no LSH candidates are found and the corpus is small, compare all pairs so demo datasets remain reliable

## Result
- repo test coverage now includes the previous failure case through the corpus CLI test
