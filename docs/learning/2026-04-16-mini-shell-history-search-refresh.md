# Mini Shell History Search Refresh and Self-Test

## Refresher notes
- Search-style history replay is easiest to reason about if it scans the stored history from newest to oldest and returns the first match.
- Reusing the already-expanded stored history entries keeps replay predictable: users re-run the exact command text that previously executed.
- Prefix search and substring search share the same core lookup idea, so a small helper keeps the behavior consistent and the errors uniform.
- It is worth validating empty search queries directly because history syntaxes that start with punctuation (`!?`) are easy to mishandle.

## Self-test
1. Why search from the end of the history list instead of the start?
   - Because shell-style replay should prefer the most recent matching command.
2. Why keep this slice full-line-only instead of supporting `sudo !!`-style inline expansion?
   - Because inline expansion needs a more complex parser and quoting model than this teaching shell currently targets.
3. Why store the expanded command in history before later replays happen?
   - Because it makes replay deterministic and lets users see the exact command text that was run.
