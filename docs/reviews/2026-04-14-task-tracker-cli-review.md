# Review log: task-tracker-cli

Date: 2026-04-14

## Pass 1 - functionality review
- Checked CRUD/status/summary flows against the intended MVP.
- Issue found: no explicit smoke-tested local install path documented.
- Fix: added package metadata, console script, and README run examples.

## Pass 2 - validation review
- Checked edge cases around invalid operations and user input.
- Issue found: blank task titles were accepted after `.strip()`.
- Fix: added `normalize_title()` validation and a test for blank titles.

## Pass 3 - portfolio/readability review
- Checked whether the project is resumable and understandable for recruiters.
- Issue found: supporting project rationale and future direction were not captured.
- Fix: added research, learning, and checklist docs to show process and next steps.
