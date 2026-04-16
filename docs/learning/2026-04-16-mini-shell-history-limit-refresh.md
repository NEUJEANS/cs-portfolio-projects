# Mini Shell History Limit Refresh and Self-Test

## Refresher notes
- Keeping a bounded history list is mostly a "keep the last N items" problem; slicing from the end is simpler and less error-prone than hand-rolling index math.
- When a persisted history file has to respect a limit, rewriting the full trimmed list is clearer than appending and then running a second cleanup pass.
- `0` is a useful edge case for retention settings because it exercises the same code path while meaning "store nothing."
- Startup trimming matters for resumability: if a history file grew before the limit was configured, loading should normalize it instead of waiting for future commands.

## Self-test
1. Why rewrite the whole history file once a limit is active?
   - Because the shell needs the on-disk file to match the already-trimmed in-memory list exactly.
2. Why is `history_limit=0` worth testing directly?
   - Because it is an easy place for accidental off-by-one behavior where one command might still leak into memory or disk.
3. Why trim history during load as well as append?
   - Because users can start a new REPL with an oversized existing history file and still expect the configured cap to take effect immediately.
