# CPU Scheduler Simulator Research — 2026-04-21 Comparison Presets and Dashboards

## Why this slice
The scheduler lab already simulated several policies well, but it still lacked a recruiter-friendly way to compare them on the same workload. The next useful step was to make the tradeoffs visible without forcing someone to run five commands and manually diff the output.

## Brief references reviewed
- UIC operating-systems lecture notes emphasize that scheduler design trades off throughput, waiting time, response time, and dispatcher overhead rather than optimizing one metric in isolation.
- The same notes call out dispatch latency as real overhead, which supports keeping the earlier explicit context-switch model in the comparison output.
- Short-job and interactive workloads are where preemption helps most, while long CPU-bound leaders create convoy-style waiting for later short jobs.

## Modeling choice for this slice
- Add committed preset workloads instead of random generation first so every comparison screenshot is reproducible.
- Keep the preset set small and narrative-driven: convoy pressure, interactive bursts, and priority-aging pressure.
- Add a first-class `compare` mode that runs the same workload through multiple algorithms with shared `--quantum`, `--aging-interval`, and `--context-switch-cost` settings.
- Highlight practical comparison metrics recruiters can read quickly: average turnaround, average waiting, average response, worst-case waiting, CPU utilization, scheduler overhead, throughput, and total time.
- Prefer those concrete metrics over a more abstract fairness formula for now, because they map directly to the OS concepts already taught in the README and test suite.

## What this should improve
- makes the project easier to demo in one command
- gives the repo portfolio-grade Markdown, HTML, and JSON artifacts instead of raw terminal output only
- creates a clean base for future fairness-score overlays or MLFQ comparisons
