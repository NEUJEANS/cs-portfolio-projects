# CPU Scheduler Simulator Research — 2026-04-21 MLFQ Slice

## Why this slice
The scheduler lab already covered FCFS, SJF, SRTF, priority aging, RR, and multi-scenario benchmarking, but it still missed one of the most recognizable interview and operating-systems teaching schedulers: MLFQ. Adding it makes the comparison pack feel more complete and gives the benchmark bundle a stronger interactive-vs-overhead story.

## Brief references reviewed
- OSTEP's MLFQ chapter refreshes the canonical rules: always run the highest-priority ready queue, use round robin within a queue, place new jobs at the top, demote jobs that burn through their allotment, and periodically boost every runnable job back to the top queue to limit starvation.
- University lecture-note summaries of MLFQ make the same practical point: short quanta near the top improve responsiveness, while longer lower-priority quanta reduce context-switch churn for CPU-bound work.

## Modeling choices for this repo
- Keep the workload model CPU-only and deterministic, so MLFQ remains easy to test and compare beside the other algorithms already in the project.
- Expose `--mlfq-quantums` instead of hard-coding one ladder, because the artifact bundle is more useful when the queue design is visible and reproducible.
- Keep a default global boost enabled (`12`) so the portfolio story matches the common anti-starvation explanation instead of shipping a starvation-prone variant by default.
- Use a moderate default ladder (`2,4,8`) instead of an ultra-short `1,2,4` ladder because the benchmark pack already charges explicit context-switch overhead, and the wider ladder tells a cleaner response-vs-overhead story.

## What this should improve
- fills a conspicuous OS-scheduler gap in the project lineup
- makes the comparison and benchmark artifacts feel more curriculum-complete
- gives the benchmark pack a clearer example of a policy that optimizes response time more aggressively than FCFS, SJF, or plain RR
