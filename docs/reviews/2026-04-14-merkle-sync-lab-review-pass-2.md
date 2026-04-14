# Review Pass 2 - merkle-sync-lab

## Focus
CLI behavior and interoperability between live directories and saved manifests.

## Findings
- The tool should accept either a directory path or a saved manifest path for diff inputs.
- JSON output is the best stable interface for future automation.

## Fixes applied
- added `resolve_manifest()` so `diff` works on either source type
- added `--json` output mode for machine-readable summaries
