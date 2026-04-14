# File Integrity Monitor Review Pass 1

## Focus
API and data-format review after the manifest upgrade.

## Findings
1. `diff_snapshots()` assumed the new manifest shape and would break on legacy baselines that stored plain `{"path": "hash"}` pairs.

## Fixes Applied
- added `_hash_value()` and compatibility handling so both v1-style flat snapshots and v2 manifests can be diffed safely.

## Result
- backward compatibility preserved while keeping the richer manifest format.
