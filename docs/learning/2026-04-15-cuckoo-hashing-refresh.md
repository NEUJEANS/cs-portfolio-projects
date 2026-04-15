# 2026-04-15 Cuckoo hashing refresh and self-test

## Refresh
- `hashlib.blake2b(..., digest_size=8)` is a simple way to derive deterministic 64-bit hash values without third-party dependencies.
- `argparse` subcommands keep the CLI demoable and align with the rest of the repo.
- JSON snapshots are enough for resumable labs as long as save/load paths create parent directories and reject malformed states.

## Self-test
1. Why can lookup stay O(1) in cuckoo hashing?
   - Because a key only needs to be checked in a fixed number of candidate positions determined by its hash functions.
2. What causes a rehash?
   - An insertion displacement chain that fails to find an empty slot within the configured attempt budget, which signals a likely cycle or too-high load.
3. Why store salts in the snapshot?
   - So a reloaded table uses the same candidate positions and can reproduce the saved placement deterministically.
