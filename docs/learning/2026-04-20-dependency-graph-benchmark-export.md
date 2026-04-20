# Dependency graph planner benchmark export refresh — 2026-04-20

## Short refresh
- `csv.DictWriter` is a good fit when the benchmark payload is already normalized into stable row dictionaries and we want deterministic header order.
- Repo-relative display labels matter for committed artifacts: absolute temp paths make GitHub screenshots and checked-in JSON snapshots noisy and non-portable.
- For this project, aggregate CSV and per-scenario strategy CSV serve different purposes: one is a leaderboard summary, the other is the plotting/notebook-friendly long-form table.
- If the CLI gains new command-specific output flags, the regression suite should cover both happy-path artifact writing and invalid use on the wrong subcommand.

## Self-test
1. Why keep both aggregate and per-strategy CSV exports?
   - The aggregate file is compact for leaderboard summaries, while the per-strategy file preserves one row per scenario/strategy pair for plotting and deeper analysis.
2. Why should committed benchmark JSON use repo-relative graph paths instead of temp-directory paths?
   - Repo-relative labels keep the artifacts readable, reproducible, and reviewable after they are checked into Git.
3. What regression is easy to miss when adding new CLI output flags?
   - The flags may work on the intended command but accidentally be accepted on unrelated commands unless misuse coverage is added.
