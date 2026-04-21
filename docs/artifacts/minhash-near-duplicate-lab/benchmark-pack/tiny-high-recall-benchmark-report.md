# MinHash benchmark summary

- Documents scanned: 4
- Shingle size: 2
- Token mode: word
- Normalize identifiers: False
- Normalize literals: False
- Signature hashes: 64
- Bands: 8
- Threshold: 0.3
- Seed: 0
- All pairs: 6
- Candidate pairs: 1
- Exact pairs above threshold: 1
- LSH pairs above threshold: 1
- LSH recall vs exact: 1.0
- Candidate reduction ratio: 0.8333

## Timings

- Build signatures: 0.002995s
- LSH candidate generation: 0.000081s
- Exact all-pairs scan: 0.000033s

## Top exact matches

- docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/tiny-high-recall/plan_a.txt <> docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/tiny-high-recall/plan_b.txt | exact=0.6000 estimated=0.6094 shared_bands=1

## Top LSH matches

- docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/tiny-high-recall/plan_a.txt <> docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/tiny-high-recall/plan_b.txt | exact=0.6000 estimated=0.6094 shared_bands=1
