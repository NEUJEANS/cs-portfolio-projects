# 2026-04-17 branch-predictor-lab research notes

## Sources consulted
- Wikipedia — Branch predictor: https://en.wikipedia.org/wiki/Branch_predictor
- Dan Luu — Branch prediction: https://danluu.com/branch-prediction/
- gem5 doxygen — TournamentBP: https://doxygen.gem5.org/develop/classgem5_1_1branch__prediction_1_1TournamentBP.html
- gem5 doxygen — LocalBP: https://doxygen.gem5.org/develop/classgem5_1_1branch__prediction_1_1LocalBP.html

## Brief takeaways
- Two-bit saturating counters are a better teaching baseline than one-bit tables because loop-closing branches usually pay only one miss on the exit instead of two misses across exit plus re-entry.
- Predictor tables are typically indexed by instruction-address bits, which makes aliasing and table-size choices meaningful in even a small simulator.
- Global-history designs such as gshare are worth including because they show how correlated patterns can beat purely per-address bias tracking without needing a huge implementation.
- A tournament predictor is a natural next slice once local-history and global-history predictors exist, because the chooser table makes hybrid behavior inspectable without needing a full simulator like gem5.

## Slice decision
Build a compact Python lab with:
- simple local trace parsing
- always-taken / always-not-taken baselines
- one-bit and two-bit bimodal predictors
- gshare as the first genuinely history-aware follow-up
- a local-history and tournament follow-up so the project covers the classic local/global/hybrid progression
- JSON-friendly output so the project can later grow artifact exports or benchmarking
- reuse the same compare payload for Markdown/SVG report cards instead of inventing a separate artifact-only path
