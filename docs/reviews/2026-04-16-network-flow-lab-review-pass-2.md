# network-flow-lab review pass 2 — 2026-04-16

## Focus
CLI/docs/checklist consistency audit.

## Issue found
The implementation exposed new benchmark families, but the project docs still described benchmarking as DAG-only and the checklist had the stress-case benchmark slice listed as unfinished.

## Fix
- updated the README intro, features, usage examples, and design notes to describe `dag`, `dense`, and `layered` benchmark families
- marked the benchmark stress-case slice complete in `projects/network-flow-lab/CHECKLIST.md`
- synced the repo-level checklist entry in `docs/checklists/network-flow-lab.md`

## Result
The code, README, and checklist now tell the same story, so the slice is resumable and portfolio-facing docs match the shipped CLI.
