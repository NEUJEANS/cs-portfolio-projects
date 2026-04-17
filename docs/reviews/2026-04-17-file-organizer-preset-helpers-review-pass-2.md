# Review pass 2 — file-organizer preset helpers — 2026-04-17

## Focus
CLI validation and error-message quality for unsupported preset names.

## Findings
1. **Validation gap:** there was no regression coverage confirming that both direct preset loads and preset-export helpers reject unknown preset names with a helpful supported-preset list.

## Fixes made
- added regression coverage for `loadPresetBucketConfig('unknown-preset')`
- added regression coverage for `writePresetConfig('unknown-preset', ...)`
- verified both paths surface the supported preset names in the thrown error message

## Verification
- `npm test --prefix projects/file-organizer-cli`
