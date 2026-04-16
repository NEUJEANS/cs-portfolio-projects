# Mini Shell History Refresh and Self-Test

## Refresher notes
- Interactive shell history is session state, so the cleanest shape for this project is to keep a shared Python list in the REPL and pass it into command execution.
- History expansion should happen before token parsing, because `!!` and `!N` conceptually replace the whole input line with an earlier command.
- Storing the expanded command instead of the literal recall token keeps later replays stable and avoids confusing chains like a history entry that still contains `!!`.
- For a compact teaching shell, full-line recall is a better slice boundary than trying to emulate all of Bash's inline history substitution rules.

## Self-test
1. Why expand `!!` before `parse_command()`?
   - Because replay should substitute the previous command line before tokenization and execution.
2. Why record the expanded command instead of the literal `!!` token?
   - So the history list shows what actually ran and later replays do not depend on nested expansion.
3. Why keep history in memory instead of adding a history file immediately?
   - In-memory history delivers a meaningful interactive shell upgrade now without introducing file-format, merge, and persistence edge cases in the same slice.
