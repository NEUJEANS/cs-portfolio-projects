# Review Pass 1 — merkle-sync-lab chunk-proof slice

## Checks
- read the new chunk-proof functions and CLI plumbing
- reran the project unit suite after adding proof coverage

## Issue found
- chunk-proof generation accepted invalid chunk sizes implicitly, which would have hidden caller mistakes

## Fix applied
- added an explicit positive chunk-size validation guard in `read_file_chunks`
