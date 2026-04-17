# 2026-04-17 branch predictor perceptron slice research

## Sources consulted
- Wikipedia — Branch predictor: https://en.wikipedia.org/wiki/Branch_predictor
- Dan Luu — Branch prediction: https://danluu.com/branch-prediction/

## Brief takeaways
- Bimodal and gshare-style predictors remain good teaching baselines, but they still rely on table lookups over short encoded histories rather than a learned weighted combination of long-history bits.
- A perceptron predictor is useful in a portfolio project because it shows the jump from classic counter-based predictors to a small neural-style classifier without requiring a full CPU simulator.
- The strongest demo case is a linearly separable long-history branch pattern: that keeps the workload reproducible and makes it obvious why weighted history can beat simple table counters.
- A perceptron slice should expose inspectable model state such as threshold, weight limit, non-zero weights, and final history so the output stays interview-friendly instead of becoming a black box.

## Slice decision
Ship a perceptron follow-up for `branch-predictor-lab` by:
- adding a perceptron predictor alongside the existing simple/local/global/hybrid suite
- generating a reproducible `perceptron-majority` synthetic workload that favors weighted long-history reasoning
- extending tests and CLI JSON output so the perceptron state is inspectable
- committing a gallery artifact card for the new workload so the slice is visible from the portfolio docs
