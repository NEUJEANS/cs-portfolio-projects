# Wrap-up — 2026-04-15T07:38:40Z

## Project
file-integrity-monitor

## What changed
- added HMAC-signed manifest support with `--signing-key-env`
- added `verify` command plus dedicated invalid-signature exit code
- prevented false-positive diffs when the baseline file lives inside the scanned directory
- expanded README, checklist, learning note, and 3 review-pass notes
- expanded automated coverage for signed scan/diff/verify flows and embedded-baseline handling

## Tests and reviews run
- `python3 -m unittest discover -s projects/file-integrity-monitor -p 'test_*.py'`
- `python3 -m py_compile projects/file-integrity-monitor/integrity_monitor.py projects/file-integrity-monitor/test_integrity_monitor.py`
- manual signed scan/verify/diff smoke test with an embedded baseline path
- review pass 1: signed baseline workflow and false-positive diff behavior
- review pass 2: CLI ergonomics and regression coverage
- review pass 3: documentation and portfolio presentation alignment
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- `cece1347f41c9020b57f43b3366c1672390e0347`

## Next step
- upgrade this project from shared-secret HMAC signing to asymmetric signatures or managed key rotation for a stronger security story
