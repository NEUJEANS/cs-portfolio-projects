# 2026-04-14 Merkle Sync Refresh

## Topics refreshed
- `hashlib.sha256()` streaming file hashing
- deterministic directory traversal with `Path.rglob()` and sorted relative paths
- simple recursive bottom-up digest construction
- `argparse` subcommands for `build` and `diff`

## Quick self-test
1. Why sort child paths before hashing a directory?
   - To keep the digest stable regardless of filesystem traversal order.
2. Why include child path names as well as digests in the directory hash input?
   - So renames and structural changes affect the parent digest even if file contents stay the same.
3. What makes Merkle-style summaries useful for sync?
   - If a subtree digest matches, the whole subtree can be skipped without re-checking every nested file.
