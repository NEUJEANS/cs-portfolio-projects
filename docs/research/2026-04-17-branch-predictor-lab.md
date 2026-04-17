# 2026-04-17 branch-predictor-lab research notes

## Sources consulted
- Wikipedia — Branch predictor: https://en.wikipedia.org/wiki/Branch_predictor
- Dan Luu — Branch prediction: https://danluu.com/branch-prediction/

## Brief takeaways
- Two-bit saturating counters are a better teaching baseline than one-bit tables because loop-closing branches usually pay only one miss on the exit instead of two misses across exit plus re-entry.
- Predictor tables are typically indexed by instruction-address bits, which makes aliasing and table-size choices meaningful in even a small simulator.
- Global-history designs such as gshare are worth including because they show how correlated patterns can beat purely per-address bias tracking without needing a huge implementation.

## Slice decision
Build a compact Python lab with:
- simple local trace parsing
- always-taken / always-not-taken baselines
- one-bit and two-bit bimodal predictors
- gshare as the first genuinely history-aware follow-up
- JSON-friendly output so the project can later grow artifact exports or benchmarking
