# Review pass 3 — MinHash mixed-language preset

## Focus
End-to-end mixed-corpus behavior.

## Findings
1. Needed verification that the new preset and comma-separated glob support work together through the CLI, not just through internal helpers.

## Fixes
- Added an end-to-end CLI regression test that writes the mixed-language preset and scans it with `--glob '*.md,*.py,*.ipynb'`.
