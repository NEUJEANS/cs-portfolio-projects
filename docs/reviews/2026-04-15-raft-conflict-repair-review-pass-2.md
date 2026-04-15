# Review pass 2 — scenario and regression audit

## Focus
Check whether the new conflict-repair slice is visible and reproducible from tests and scenario flows, not just by direct in-memory mutation.

## Findings
1. The first regression test only proved repair through direct object mutation.
2. That made the feature harder to demo from the CLI or explain in portfolio screenshots.

## Fixes applied
- Added a lab-only `force-log` scenario action to inject a divergent follower suffix for teaching/demo purposes.
- Added a `run_scenario` regression test that uses `force-log` and validates both `log_forced` and `append_rejected` events.

## Result
The repair path is now externally scriptable, which makes the project stronger as a teaching artifact.
