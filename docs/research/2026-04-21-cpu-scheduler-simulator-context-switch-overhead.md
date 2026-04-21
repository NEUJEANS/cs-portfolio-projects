# CPU Scheduler Simulator Research — 2026-04-21 Context-Switch Overhead

## Why this slice
The scheduler project had solid policy coverage, but it still treated every algorithm as if dispatching were free. That made Round Robin and preemptive policies look cleaner than they would under even a tiny fixed switch cost.

## Brief references reviewed
- Context switching saves one execution state and restores another, which creates real CPU overhead rather than useful application work.
- Scheduling goals still trade off throughput, response time, and fairness, so adding a dispatch-cost knob is a practical way to show that better responsiveness can come with extra scheduler churn.

## Modeling choice for this slice
- Add a fixed `--context-switch-cost` in time units.
- Charge it only when the CPU moves between two different runnable processes.
- Represent that time explicitly as `CS` in the timeline.
- Exclude `CS` time from useful CPU utilization, but report it separately as scheduler overhead.
- Keep the model intentionally simple by skipping idle-to-process dispatch cost so policy-to-policy comparisons stay easy to read.

## What this should improve
- makes Round Robin and preemptive behavior look more realistic
- gives the README a stronger systems-story talking point
- creates a clean bridge to future fairness-vs-overhead dashboards
