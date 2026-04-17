# file-organizer-cli checklist

## Completed slices
- [x] extension-based bucket organizer with dry-run previews
- [x] recursive traversal that skips reserved bucket folders
- [x] collision-safe moves with cross-device fallback handling
- [x] JSON/text reporting plus manifest export
- [x] manifest-driven undo with collision-safe restores and empty-dir cleanup
- [x] config-driven custom buckets and fallback bucket overrides
- [x] built-in presets with `--preset`, `--list-presets`, and `--write-preset`
- [x] CI-friendly shared-config linting with `--lint-config`
- [x] normalized-config helpers with in-place `--fix-config` and exported `--write-normalized-config`
- [x] normalization preview mode with `--preview-normalized-config` rewrite summaries before editing shared JSON
- [x] regression coverage for preset export/import, lint warnings/errors, invalid config guards, and normalized-config writes

## Current demo-ready flow
- [x] organize a loose folder with a built-in preset
- [x] export the preset to JSON for teammates
- [x] lint the shared config in CI or pre-commit
- [x] preview normalization changes before editing a shared config
- [x] auto-fix or export a canonical normalized config for teammates
- [x] run organize with the shared config
- [x] undo the run from the saved manifest

## Next vertical slices
- [ ] support richer matching rules beyond plain extensions (for example basename patterns or MIME-aware detection)
- [ ] add a small publishable demo artifact set that shows before/after folder trees and config preview output for the README and portfolio screenshots
