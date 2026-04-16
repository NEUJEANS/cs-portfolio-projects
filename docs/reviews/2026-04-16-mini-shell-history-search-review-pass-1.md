# Mini Shell History Search Review — Pass 1

## Findings
1. The new `!prefix` behavior needed a regression test proving it prefers the most recent matching command rather than the oldest one.
2. Without that test, the feature could silently drift away from the shell-style lookup rule during a refactor.

## Fixes applied
- added a focused unit test that seeds multiple matching commands and verifies `!echo` replays the newest matching entry

## Result
The prefix-replay feature is now pinned to the intended newest-first behavior.
