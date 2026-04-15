# 2026-04-15 12:16 UTC — distributed-snapshot-lab failure/recovery slice

## What changed
- added process liveness tracking (`up` / `down`) to `distributed-snapshot-lab`
- added `fail_process` / `recover_process` behaviors and timeline events
- added CLI support for `--fail` / `--recover` on existing flows
- added a new `script` subcommand for replayable `send` / `deliver` / `fail` / `recover` / `snapshot` scenarios
- exposed `process_statuses` in snapshot and script JSON output
- extended Mermaid rendering with FAIL/RECOVER notes and status summaries
- updated README, research, learning, checklist, and review notes for resumability

## Tests and reviews run
- `python3 -m unittest discover -s projects/distributed-snapshot-lab -p 'test_*.py' -v`
- scripted CLI smoke check for outage -> recovery -> snapshot flow
- review pass 1: fixed send semantics so only the sender must be live
- review pass 2: fixed missing snapshot state for down processes during marker traversal
- review pass 3: audited CLI/docs/demo clarity and confirmed no further code changes were needed
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`

## Commit hash
- feature commit: `0ae58dc` — Add failure recovery scripting to distributed snapshot lab

## Next step
- model explicit network partitions or link-level failures separately from whole-process outages
