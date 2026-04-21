# MinHash benchmark summary

- Documents scanned: 8
- Shingle size: 3
- Token mode: word
- Normalize identifiers: False
- Normalize literals: False
- Signature hashes: 64
- Bands: 8
- Threshold: 0.25
- Seed: 0
- All pairs: 28
- Candidate pairs: 1
- Exact pairs above threshold: 2
- LSH pairs above threshold: 1
- LSH recall vs exact: 0.5
- Candidate reduction ratio: 0.9643

## Timings

- Build signatures: 0.006900s
- LSH candidate generation: 0.000131s
- Exact all-pairs scan: 0.000057s

## Top exact matches

- docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/frontend_a.txt <> docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/frontend_b.txt | exact=0.7333 estimated=0.7188 shared_bands=1
- docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/etl_a.txt <> docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/etl_b.txt | exact=0.2727 estimated=0.2656 shared_bands=0

## Top LSH matches

- docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/frontend_a.txt <> docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/frontend_b.txt | exact=0.7333 estimated=0.7188 shared_bands=1
