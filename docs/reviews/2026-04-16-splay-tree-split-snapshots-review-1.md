# Review Pass 1 — 2026-04-16 — splay-tree-lab split snapshot persistence

## Focus
- verify the new `split` CLI flags and persisted snapshot payload shape

## What I checked
- read the updated CLI parser and split execution path
- ran a manual split with `--left-output` and `--right-output`
- loaded both persisted snapshots with `show`

## Issue found
- tests assumed a fixed `right_root`, but the miss-splay tree shape makes that root depend on the current tree shape

## Fix applied
- changed tests to validate correctness/resumability (`root` matches payload and belongs to that partition) instead of hard-coding a single root value
