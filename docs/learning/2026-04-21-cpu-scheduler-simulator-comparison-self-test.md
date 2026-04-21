# CPU Scheduler Simulator Learning Note — 2026-04-21 Comparison Presets Self-Test

## Quick refresh
- A good scheduler comparison uses the same workload and timing knobs for every algorithm, otherwise the result is not apples-to-apples.
- Convoy-style mixes are useful because FCFS can look much worse once short jobs queue behind a long burst.
- Response time and worst-case waiting are both worth surfacing, because an algorithm can improve the first response for some jobs while still hurting the tail.

## Self-test
1. **Q:** Why add committed preset workloads before random generation?  
   **A:** Because committed presets make screenshots, docs, and tests reproducible across runs and across machines.

2. **Q:** Why keep context-switch cost inside compare mode instead of stripping it out?  
   **A:** Because the interesting tradeoff is exactly fairness or responsiveness versus scheduler churn, so the dashboard should expose that cost directly.

3. **Q:** Why include worst-case waiting alongside averages?  
   **A:** Because averages can hide starvation-like tails, while worst-case waiting makes the ugly edge cases obvious in a portfolio demo.
