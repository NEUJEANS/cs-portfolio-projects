# 2026-04-19 dependency graph diagram refresh + self-test

## Goal
Refresh the smallest Mermaid/DOT rules needed to ship a deterministic diagram export for `dependency-graph-planner`.

## Quick refresh
- Mermaid flowcharts can use stable synthetic node IDs while displaying richer quoted labels, which avoids collisions when task names contain punctuation or spaces.
- Mermaid labels should stay compact and escaped for quotes/HTML entities because the exporter is generating text, not hand-authored diagrams.
- Graphviz DOT accepts quoted node IDs, so task names can stay human-readable while attributes carry styling such as `peripheries=2` or `penwidth=2` for critical-path emphasis.
- Same-rank DOT subgraphs are enough to communicate parallel layers without inventing a second scheduling model.

## Self-check
1. Why generate synthetic Mermaid node IDs instead of deriving them from task names?  
   To avoid collisions and punctuation issues while still rendering readable task labels.
2. Why keep DOT export text-only instead of rendering images inside the project?  
   Plain-text DOT is deterministic, dependency-light, testable, and can be rendered later by any Graphviz tool.
3. What makes the diagram export more than a cosmetic feature here?  
   It reuses computed layers, durations, and critical-path metadata so the visuals explain actual scheduling analysis instead of duplicating raw edges only.
