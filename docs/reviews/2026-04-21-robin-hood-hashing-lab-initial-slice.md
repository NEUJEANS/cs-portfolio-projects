# robin-hood-hashing-lab initial slice review log

## Review pass 1 — snapshot validation strictness
- Checked whether persisted snapshots fail loudly on malformed payloads instead of silently coercing values.
- Issue found: `from_snapshot(...)` converted `key` and `value` fields with `str(...)`, which would have accepted non-string payloads and hidden bad snapshot data.
- Fix applied: required string key/value fields explicitly and added a regression test that rejects non-string payload values.

## Review pass 2 — benchmark artifact completeness
- Checked whether the benchmark workflow produced both human-readable and machine-readable outputs suitable for committed portfolio artifacts.
- Issue found: the initial CLI tests only covered CSV benchmark output, so the JSON export path was unverified even though the code supported it.
- Fix applied: added CLI regression coverage for `.json` benchmark exports and committed both `sample-benchmark.csv` and `sample-benchmark.json` under `docs/artifacts/robin-hood-hashing-lab/`.

## Review pass 3 — README/checklist alignment
- Audited the project README, top-level README, and checklist against the final command surface and generated artifacts.
- Issue found: the first README draft did not mention automatic resize behavior during `build`, the committed sample artifact paths, or the new project entry in the repo progress list.
- Fix applied: updated the project README with resize/artifact notes, added the sample artifact section, updated the checklist wording, and registered `robin-hood-hashing-lab` in the root `README.md` progress tracker.
