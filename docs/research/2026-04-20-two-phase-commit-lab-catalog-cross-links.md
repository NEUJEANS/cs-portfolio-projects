# Two-phase commit lab research — 2026-04-20 — catalog cross-links

## Why no external web research this slice
- This slice does not change distributed-transaction semantics.
- The work is limited to deterministic artifact discovery and Markdown linking around already-reviewed 2PC, comparison, and termination outputs.

## Internal references reviewed
- `projects/two-phase-commit-lab/two_phase_commit_lab.py`
  - existing catalog generation flow, report naming, and comparison/termination filename conventions
- `docs/artifacts/two-phase-commit-lab/`
  - the current committed artifact set, especially `_report.md`, `_protocol_compare.{md,html}`, and `_termination.md`

## Slice decision
- Keep companion discovery convention-based and file-existence-based so the catalog stays deterministic and requires no extra metadata file.
- Link only committed artifacts that actually exist beside the catalog/report bundle.
