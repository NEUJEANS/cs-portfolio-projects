# Learning refresh — 2026-04-18 — page replacement aggregate dashboard

## Quick refresher
- Cross-workload comparisons should **normalize** by reference length; otherwise long traces dominate raw page-fault totals.
- For this project, a good portfolio metric is the **average page-fault rate across the studied frame range**.
- Showing all workloads in one chart is useful, but the chart needs the same frame range for every workload so the comparison stays fair.
- Pairing the normalized chart with winner counts and anomaly counts makes the dashboard easier to explain in a presentation.

## Self-check
If workload A averages `6` faults over a `12`-reference trace and workload B averages `18` faults over a `60`-reference trace:
- workload A average fault rate = `50%`
- workload B average fault rate = `30%`
- workload B has more raw faults, but workload A is still the worse normalized locality case

## Why this slice matters
- The gallery already explains one workload at a time; this slice gives a **single slide-ready summary** across presets and benchmarks.
- It turns the simulator into something stronger for portfolio write-ups and interviews because the student can explain both per-workload behavior and cross-workload trends.
- It keeps the project ready for a later slice like working-set policies or richer trace-summary cards.
