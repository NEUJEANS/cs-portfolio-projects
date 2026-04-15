# Review pass 3 — shamir authenticated bundles

## Checks
- reviewed bundle metadata validation paths
- tested malformed bundle metadata scenarios

## Issue found
- `load_shares` trusted `prime` and `share_count` metadata instead of validating them against the supported field and actual bundle contents

## Fix
- added validation for `prime == 257`
- added validation that `share_count` matches the number of serialized shares
- added tests covering mismatched `share_count` metadata
