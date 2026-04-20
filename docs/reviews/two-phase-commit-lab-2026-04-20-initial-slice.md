# Two-phase commit lab review — 2026-04-20 — initial slice

## Pass 1 — automation-friendly CLI output
- Re-ran the new `run --json --markdown-out ...` path as if a script were generating artifact files and parsing stdout at the same time.
- Issue found: the CLI printed the "wrote Markdown report" status line to stdout before the JSON payload, which made the machine-readable output brittle for automation and test fixtures.
- Fix: changed the status line to go to `stderr` whenever `--json` is active, so stdout stays clean JSON while still reporting artifact creation to humans.

## Pass 2 — artifact readability polish
- Read the generated blocking-case Markdown report directly in `docs/artifacts/two-phase-commit-lab/` instead of assuming the renderer spacing was fine.
- Issue found: the optional blocking-reason bullet ran directly into the `## Participant summary` heading, which made the committed artifact feel less polished than the rest of the repo.
- Fix: simplified `render_markdown_report(...)` to build the section list explicitly and always insert a blank line before the participant table.

## Pass 3 — repo-level discoverability and regression coverage
- Re-read the root README and the new trace-oriented tests from the perspective of future maintenance.
- Issue found: the new project was not yet visible in the top-level progress list, and the abort-path test was overly tied to one exact trace index instead of the user-facing global-abort wording.
- Fix: added `two-phase-commit-lab` to the repo README and relaxed the abort regression check so it asserts the presence of the global-abort explanation without depending on fragile event numbering.

## Final verification
- `python3 -m py_compile projects/two-phase-commit-lab/two_phase_commit_lab.py tests/test_two_phase_commit_lab.py`
- `python3 -m unittest tests.test_two_phase_commit_lab -v`
- regenerated committed sample reports under `docs/artifacts/two-phase-commit-lab/`
- deterministic double-export hash check for all four committed Markdown report artifacts
- `git diff --check`
