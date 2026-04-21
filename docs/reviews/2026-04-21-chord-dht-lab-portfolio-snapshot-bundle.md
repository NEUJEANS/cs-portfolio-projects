# chord-dht-lab portfolio snapshot bundle review log

## Review pass 1 — bundle manifest completeness
- Checked the new bundle helper end to end against the generated `manifest.json`.
- Issue found: the manifest initially serialized before its own artifact row was appended, so the manifest output did not describe itself.
- Fix applied: append both the index and manifest artifact rows before rendering/writing the bundle metadata.

## Review pass 2 — README/checklist alignment
- Checked the project README and checklist against the new command surface.
- Issue found: the README still treated portfolio snapshot bundling as a future improvement and did not show the new one-command workflow.
- Fix applied: added the `portfolio-snapshot` feature/usage example and replaced the future-improvement note with the next logical artifact gap.

## Review pass 3 — determinism and committed sample artifacts
- Re-ran the bundle command twice into the same temporary directory and compared SHA-256 hashes for every generated file.
- Issue found: before this slice there was no committed sample bundle to demonstrate the new workflow in the repo.
- Fix applied: generated and committed `docs/artifacts/chord-dht-lab/sample-portfolio-snapshot/` and verified repeated runs remain byte-stable.
