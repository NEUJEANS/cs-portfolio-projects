# Review Pass 2 — 2026-04-16 — splay-tree-lab benchmark artifact export

## Focus
- docs/CLI alignment for the new JSON + CSV artifact workflow

## What I checked
- compared README usage examples against the actual `argparse` flags
- checked the feature list and future-work section for stale statements
- confirmed the slice checklist and learning refresh note describe the same scope as the code

## Issue found
- the README still described benchmark artifact export as future work, which would make the new slice look unfinished

## Fix applied
- added a concrete benchmark export example to the README feature/usage sections and replaced the stale future-work item with the next stronger follow-up: multi-size benchmark sweeps
