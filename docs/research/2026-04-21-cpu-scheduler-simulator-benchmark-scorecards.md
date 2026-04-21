# CPU Scheduler Simulator Research — 2026-04-21 Benchmark Scorecards Slice

## Why this slice
The scheduler lab already had a strong benchmark family pack, but the summary still leaned on dense tables. After the MLFQ slice, the weakest part of the project was no longer scheduling coverage, it was recruiter-facing storytelling. This slice focuses on making the benchmark results easier to scan and present.

## External research decision
- skipped new external web research for this run because the slice extends the repo's existing benchmark aggregation, reporting, and artifact-generation architecture directly
- the relevant domain concepts were already covered in the earlier scheduler, fairness, and MLFQ notes; this run mainly needed better packaging of evidence, not new algorithm rules

## Modeling choices for this repo
- keep the scorecards derived directly from benchmark win counts so every claim stays grounded in reproducible pack output
- limit the heatmap to headline portfolio goals: turnaround, waiting, response, fairness, throughput, and low overhead
- include both explicit counts and percentages in the heatmap cells so the artifact remains evidence-first in screenshots and static docs
- keep the new story in the benchmark bundle itself instead of inventing a separate app, which preserves the repo's lightweight CLI-first style

## What this should improve
- make the benchmark summary feel like a short operating-systems case study instead of a raw metric dump
- give the repo a screenshot-friendly artifact for README, resume, or slide reuse
- make it much faster to explain where FCFS, SJF, SRTF, RR, priority aging, and MLFQ each win or lose
