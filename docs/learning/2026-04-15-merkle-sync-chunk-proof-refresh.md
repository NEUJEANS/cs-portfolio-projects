# Merkle sync chunk-proof refresh

## Refresh points
- a file-level Merkle tree can be built from fixed-size chunk hashes, pairing adjacent nodes until one root remains
- when a level has an odd node count, duplicating the last hash is a straightforward teaching/demo strategy
- a chunk proof is just the sibling digest list plus left/right placement metadata for each level
- verification recomputes the chain upward and checks whether it matches the root digest
- chunk-diff output becomes more useful when it includes offsets, per-chunk sizes, and source-side proofs for changed chunks

## Self-test
- confirmed the implementation can verify every chunk proof for a sample file
- confirmed a two-file chunk diff reports only the mutated chunk index when one block changes
- confirmed appended source data shows up as extra changed chunk indexes on the source side
