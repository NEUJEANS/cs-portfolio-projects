# 2026-04-14 Huffman Compressor Review Log

## Pass 1 - algorithm correctness
- Checked whether the decoder rebuilds the same tree shape as the encoder.
- Found a real bug: tie-breaking in tree construction depended on insertion order, which broke some round trips.
- Fix: introduced deterministic tree construction from sorted frequency metadata and a stable node ordering field.
- Validation: `python3 -m unittest -v test_huffman_compressor.py`

## Pass 2 - local portability and developer ergonomics
- Checked whether the test command works in a minimal Python-only environment.
- Found a practical issue: `pytest` was not installed on the host, which made the original test instructions brittle.
- Fix: rewrote tests to standard-library `unittest` and updated the README test command.
- Validation: `python3 -m unittest -v test_huffman_compressor.py`

## Pass 3 - CLI and file round-trip smoke check
- Checked the actual CLI flow for compress/decompress against a temporary sample file.
- Verified archive creation, custom output path, and byte-for-byte restoration.
- Validation:
  - `python3 huffman_compressor.py compress <sample>`
  - `python3 huffman_compressor.py decompress <archive> -o <restored>`
  - `cmp <sample> <restored>`

## Final assessment
- The vertical slice is portfolio-worthy and resumable.
- The next worthwhile upgrade is adding compression-ratio reporting and canonical Huffman codes.
