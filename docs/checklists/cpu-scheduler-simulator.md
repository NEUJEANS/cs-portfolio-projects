# CPU Scheduler Simulator Checklist

## 2026-04-14 vertical slice
- [x] choose next project after the existing set reached a solid baseline
- [x] do brief scheduling research
- [x] do short Python/deque/simulation refresh and self-test
- [x] implement process model and scheduling algorithms
- [x] add CLI report and JSON output
- [x] add README with usage examples
- [x] run tests
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice
- [x] refresh SRTF preemption rules and deterministic tie-breaking
- [x] add preemptive SRTF algorithm support to the simulator and CLI
- [x] extend tests for preemption, tie-breaking, and JSON output
- [x] update README examples and feature list
- [x] run tests
- [x] complete review pass 1
- [x] complete review pass 2
- [x] complete review pass 3
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 vertical slice
- [x] identify cpu-scheduler-simulator as one of the weaker portfolio labs that still lacked priority scheduling
- [x] refresh priority scheduling and aging rules, then capture a short self-test note
- [x] add a resumable slice checklist entry
- [x] implement priority scheduling with optional aging in the simulator and CLI
- [x] extend JSON loading, reporting, and README usage examples for priority workloads
- [x] add unit and CLI tests for priority ordering, aging behavior, and validation
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 vertical slice, context-switch overhead
- [x] identify the next weakest scheduler gap after priority aging and choose context-switch overhead modeling
- [x] do brief context-switch overhead research and capture a short self-test note
- [x] add a resumable slice checklist entry
- [x] implement optional context-switch overhead accounting in the simulator and CLI
- [x] update the README and sample artifact so the new behavior is easy to demo
- [x] add unit and CLI tests for overhead timing, idle-gap behavior, repeated RR dispatches, and validation
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 vertical slice, workload presets and comparison dashboards
- [x] identify the next weakest scheduler gap after context-switch modeling and choose preset-driven side-by-side comparisons
- [x] do brief scheduler-comparison research and capture a short self-test note
- [x] add a resumable slice checklist entry
- [x] add committed workload presets that tell clear scheduler tradeoff stories
- [x] implement compare-mode Markdown, HTML, and JSON artifact generation
- [x] update the README and committed sample artifacts so the comparison flow is easy to demo
- [x] add unit and CLI tests for preset loading, compare-mode summaries, and output writing
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 vertical slice, fairness and slowdown visualization dashboard
- [x] identify the next weakest scheduler storytelling gap after comparison dashboards and choose fairness/slowdown distribution visuals
- [x] do a brief scheduler-fairness refresh and capture a short self-test note
- [x] add a resumable slice checklist entry
- [x] extend compare-mode summaries with slowdown/fairness metrics and per-process experience data
- [x] add an SVG fairness dashboard export and refresh the committed comparison artifact bundle
- [x] update the README plus comparison docs so the new visualization path is easy to demo
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 vertical slice, benchmark family pack
- [x] inspect the current scheduler project and confirm the next weak spot is multi-scenario benchmarking after the single-workload fairness dashboard
- [x] skip external web research because this slice extends the current scheduler comparison/export architecture directly
- [x] self-test the current preset compare flow before editing
- [x] add a resumable slice checklist entry
- [x] implement deterministic generated workload families and benchmark-pack aggregation mode
- [x] export a committed benchmark bundle with pack-level summaries plus per-scenario compare artifacts
- [x] update the README and project checklist notes for the new benchmark flow
- [x] run tests and deterministic artifact checks
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 vertical slice, MLFQ scheduling and benchmark integration
- [x] inspect the current scheduler project and confirm the next weak spot is missing MLFQ support after the benchmark family pack
- [x] do brief MLFQ research and capture a short self-test note
- [x] add a resumable slice checklist entry
- [x] implement a preemptive MLFQ algorithm with configurable queue quantums and periodic priority boosts
- [x] thread MLFQ through compare and benchmark flows plus recruiter-facing metadata
- [x] refresh the README and committed artifact generation commands for the new scheduler path
- [x] add unit and CLI tests for MLFQ scheduling, boost behavior, validation, and reporting
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [ ] commit and push
- [ ] append wrap-up
