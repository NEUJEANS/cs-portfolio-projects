# deadlock-detector-lab checklist

## Original build-out
- [x] choose a new OS-focused project because the existing set is already complete enough
- [x] capture short deadlock-detection research notes
- [x] do a quick operating-systems algorithm refresh and self-test
- [x] implement wait-for graph deadlock detection
- [x] implement resource-allocation deadlock detection
- [x] add sample JSON inputs and README usage examples
- [x] add automated tests for safe and deadlocked states
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 Banker trace/export slice
- [x] review the prior Banker's wrap-up and confirm the next slice should focus on trace/export support
- [x] capture short notes for step-by-step safety tracing and portfolio-friendly exports
- [x] refresh the Banker's safety flow and define what each trace step should show
- [x] implement trace steps and blocking summaries for Banker's safety analysis
- [x] extend request evaluation with trial-state trace details
- [x] add Markdown export support plus committed sample artifacts
- [x] update README usage/docs for the new trace workflow
- [x] extend automated tests for trace JSON and Markdown export behavior
- [x] run project tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 wait-for and allocation visual export slice
- [x] review the prior deadlock-detector wrap-up and confirm the next weak spot is missing visual exports
- [x] capture short notes for static SVG and HTML deadlock storytelling
- [x] refresh the SVG/HTML export approach and do a quick self-test for the process/resource visual vocabulary
- [x] implement wait-for graph SVG and HTML exports
- [x] implement resource-allocation SVG and HTML exports
- [x] commit deterministic sample visual artifacts under `docs/artifacts/deadlock-detector-lab/`
- [x] update the project README usage examples for the new visual commands
- [x] extend automated tests for the new CLI export paths
- [x] run project tests and artifact-generation smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-21 detection-vs-avoidance dashboard slice
- [x] review the prior deadlock-detector wrap-up and confirm the next weak spot is the missing combined dashboard
- [x] capture short notes for a side-by-side detection versus avoidance story
- [x] refresh the deadlock-detection vs Banker's comparison flow and define the dashboard sections
- [x] implement a combined dashboard command with Markdown and HTML exports
- [x] embed the wait-for and allocation visuals alongside Banker's safety and request traces
- [x] commit deterministic sample dashboard artifacts under `docs/artifacts/deadlock-detector-lab/`
- [x] update the project README usage examples for the new dashboard workflow
- [x] extend automated tests for the combined dashboard CLI path
- [x] run project tests and dashboard artifact-generation smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
