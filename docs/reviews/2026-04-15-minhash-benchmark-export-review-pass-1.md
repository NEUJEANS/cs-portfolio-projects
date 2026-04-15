# Review pass 1 — MinHash benchmark export

Focus: correctness of benchmark payload and export helpers.

## Checks run
- `python3 -m unittest tests.test_minhash_near_duplicate`
- `python3 -m py_compile projects/minhash-near-duplicate-lab/minhash_lab.py tests/test_minhash_near_duplicate.py`

## Findings
- Benchmark payload now includes the configuration fields needed for reusable exports (`shingle_size`, `num_hashes`, `bands`, `threshold`, `seed`).
- Export helpers cover `.json`, `.csv`, and `.md` and reject unsupported suffixes.
- No code changes were needed after this pass.
