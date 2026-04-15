# 2026-04-15 review — karger-min-cut-lab

## Review pass 1 — contraction state correctness
- Checked whether contracted edges were still referencing original vertex labels after the first merge.
- Issue found: the first implementation mixed original-vertex membership tracking with already-contracted edge labels, which produced `KeyError` failures during later contractions.
- Fix applied: keep the active edge list in current-supernode label space and remap only the two merged endpoints on each contraction step.

## Review pass 2 — exact verifier correctness
- Checked whether the brute-force exact checker enumerated cuts correctly.
- Issue found: the first subset enumeration skipped valid anchored cuts and returned incorrect values for simple graphs like a triangle-with-tail.
- Fix applied: anchor one vertex, enumerate all subsets of the remaining vertices, and skip only the all-vertices side.

## Review pass 3 — CLI/test resilience and output sanity
- Re-ran unit + CLI coverage and inspected the trace payload shape.
- Issue found: the trace payload still referenced stale variable names (`chosen_u` / `chosen_v`) after the contraction rewrite.
- Fix applied: update trace emission to record the active merged edge labels (`left` / `right`).

## Final verification
- `python3 -m unittest discover -s projects/karger-min-cut-lab -p 'test_*.py' -v`
- `python3 -m unittest discover -s tests -p 'test_*.py' -v`

## Result
- New project is stable, reproducible with seeds, and validated by both targeted and broader repository test runs.
