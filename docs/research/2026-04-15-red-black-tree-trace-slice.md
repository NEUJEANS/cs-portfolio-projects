# red-black-tree trace slice research — 2026-04-15

## Goal
Add one explainability-focused vertical slice to `red-black-tree-lab` without destabilizing the existing balanced-tree implementation.

## Notes
- A useful next slice is traceability rather than a brand-new algorithm: interviewers often care whether the student can explain *why* a repair happened, not only produce a valid tree.
- The highest-value trace events are:
  - insert recolor / triangle / line cases
  - left/right rotations
  - delete single-child vs two-child path
  - delete-fixup sibling-red / black-children / inner-red / outer-red cases
- JSON trace output is a good fit because it stays testable and can later feed a README table, animation, or Graphviz narrator.

## Decision
Implement optional `--trace` JSON output first, then leave Graphviz step-by-step rendering as a later follow-up.
