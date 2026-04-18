# Review pass 3 — file-organizer demo artifacts — 2026-04-18

## Focus
Checklist/demo-flow drift after landing the reproducible demo generator.

## Findings
1. **Checklist drift:** the file-organizer checklists marked the demo-artifacts slice as done, but the "current demo-ready flow" still stopped at organize + undo and did not mention MIME-aware runs or regenerating the published bundle.

## Fixes made
- updated `projects/file-organizer-cli/CHECKLIST.md` to include the MIME-aware run and the new publishable demo-bundle regeneration step
- updated `docs/checklists/file-organizer-cli.md` so the top-level file-organizer roadmap explicitly tracks the reproducible demo-artifact generator slice

## Verification
- reread the updated checklist sections and confirmed they match the shipped generator + committed artifact bundle
