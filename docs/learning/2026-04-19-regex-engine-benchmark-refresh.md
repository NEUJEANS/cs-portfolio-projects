# Regex engine benchmark refresh and self-test — 2026-04-19

## Refresh
- benchmark the same public operations the CLI already exposes: `fullmatch` and `search`
- reuse one compiled Thompson-NFA engine and one compiled Python `re.Pattern` per case so the timing story is about matching, not repeated parse/setup overhead
- measure short runs with `time.perf_counter()` and include a small warmup so the first call does not dominate tiny iteration counts
- keep shorthand benchmark cases ASCII-only because the lab intentionally teaches ASCII `\d` / `\w` / `\s`, while Python `re` is Unicode-aware by default

## Self-test
1. Why not benchmark raw parser construction on every iteration?
   - this slice is about matching/runtime behavior of already-compiled patterns, which is the more useful portfolio comparison here.
2. What makes a benchmark case "safe" for semantic agreement?
   - it stays inside the regular-language subset this lab implements and avoids Unicode-policy edge cases for shorthand classes.
3. What should the report show besides elapsed time?
   - agreement/mismatch with Python `re`, the concrete match result, and a readable summary that reviewers can skim without rerunning commands.
