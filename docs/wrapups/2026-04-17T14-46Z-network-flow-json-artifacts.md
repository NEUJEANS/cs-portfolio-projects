# Wrap-up — 2026-04-17 14:46 UTC

## What changed
- Safely synced `main` with `origin/main` first, confirmed there was no local/remote drift, and continued the next `network-flow-lab` vertical slice.
- Added portable `--json-out` support for flow, matching, weighted-assignment, generic min-cost-flow, and benchmark commands.
- Published committed JSON companions under `docs/artifacts/network-flow-lab/` and linked them from the assignment/cost artifact pages, the optimization gallery, the benchmark gallery, the top-level showcase, the project README, and the artifact index.
- Kept the JSON artifacts publish-safe by rebasing path-like fields to artifact-relative paths so the committed payloads do not leak absolute local filesystem paths.
- Regenerated the published proof/benchmark bundles from one stable command set so the linked JSON, Markdown, SVG, and HTML artifacts line up with each other instead of drifting across separate refreshes.

## Tests / reviews run
- `python3 -m py_compile projects/network-flow-lab/network_flow.py tests/test_network_flow_lab.py`
- `python3 -m unittest tests.test_network_flow_lab` (`71` tests)
- Artifact smoke/regeneration runs:
  - `python3 projects/network-flow-lab/network_flow.py demo --markdown-out docs/artifacts/network-flow-lab/sample-flow-proof.md --svg-out docs/artifacts/network-flow-lab/sample-flow-proof.svg --json-out docs/artifacts/network-flow-lab/sample-flow-result.json`
  - `python3 projects/network-flow-lab/network_flow.py match-demo --markdown-out docs/artifacts/network-flow-lab/sample-matching-proof.md --svg-out docs/artifacts/network-flow-lab/sample-matching-proof.svg --json-out docs/artifacts/network-flow-lab/sample-matching-result.json`
  - `python3 projects/network-flow-lab/network_flow.py assign-demo --dot-out docs/artifacts/network-flow-lab/sample-assignment.dot --markdown-out docs/artifacts/network-flow-lab/sample-assignment-proof.md --svg-out docs/artifacts/network-flow-lab/sample-assignment-proof.svg --html-out docs/artifacts/network-flow-lab/sample-assignment-artifact-page.html --json-out docs/artifacts/network-flow-lab/sample-assignment-result.json`
  - `python3 projects/network-flow-lab/network_flow.py cost-demo --dot-out docs/artifacts/network-flow-lab/sample-cost-flow.dot --markdown-out docs/artifacts/network-flow-lab/sample-cost-flow-proof.md --svg-out docs/artifacts/network-flow-lab/sample-cost-flow-proof.svg --html-out docs/artifacts/network-flow-lab/sample-cost-flow-artifact-page.html --json-out docs/artifacts/network-flow-lab/sample-cost-flow-result.json`
  - `python3 projects/network-flow-lab/network_flow.py benchmark --nodes 24 --edge-probability 0.18 --trials 5 --seed 42 --graph-family dag --markdown-out docs/artifacts/network-flow-lab/benchmark-dag-report.md --svg-out docs/artifacts/network-flow-lab/benchmark-dag-report.svg --json-out docs/artifacts/network-flow-lab/benchmark-dag-report.json`
  - `python3 projects/network-flow-lab/network_flow.py benchmark --nodes 18 --edge-probability 0.30 --trials 3 --seed 7 --graph-family dense --markdown-out docs/artifacts/network-flow-lab/benchmark-dense-report.md --svg-out docs/artifacts/network-flow-lab/benchmark-dense-report.svg --json-out docs/artifacts/network-flow-lab/benchmark-dense-report.json`
  - `python3 projects/network-flow-lab/network_flow.py benchmark --nodes 18 --edge-probability 0.20 --trials 3 --seed 7 --graph-family layered --markdown-out docs/artifacts/network-flow-lab/benchmark-layered-report.md --svg-out docs/artifacts/network-flow-lab/benchmark-layered-report.svg --json-out docs/artifacts/network-flow-lab/benchmark-layered-report.json`
  - `python3 projects/network-flow-lab/network_flow.py gallery-demo --artifact-dir docs/artifacts/network-flow-lab --html-out docs/artifacts/network-flow-lab/artifact-gallery.html`
  - `python3 projects/network-flow-lab/network_flow.py benchmark-gallery-demo --artifact-dir docs/artifacts/network-flow-lab --html-out docs/artifacts/network-flow-lab/benchmark-gallery.html`
  - `python3 projects/network-flow-lab/network_flow.py showcase-demo --artifact-dir docs/artifacts/network-flow-lab --html-out docs/artifacts/network-flow-lab/showcase.html`
- Review pass 1: portable-path audit on committed JSON artifacts; found `json_output` stayed cwd-relative inside published files, then fixed serialization so path-like fields are rebased relative to the artifact file itself.
- Review pass 2: JSON-link coverage audit across README, artifact pages, galleries, and showcase.
- Review pass 3: HTML local-link validation script over `artifact-gallery.html`, `benchmark-gallery.html`, `showcase.html`, `sample-assignment-artifact-page.html`, and `sample-cost-flow-artifact-page.html` verified every local `href`/`src` target exists.
- Final consistency refresh: regenerated the committed proof/benchmark artifacts with stable parameters (`dinic` for the flow/matching demos; original seeded benchmark suites for `dag`, `dense`, and `layered`) so the published Markdown/SVG/JSON companions match.

## Implementation commits
- `dba141c` — `feat(network-flow-lab): add JSON artifact companions`
- `1fce7da` — `fix(network-flow-lab): align published artifact bundles`

## Next step
- Add a small input-editor/replay surface to the showcase so reviewers can tweak a sample graph and compare a fresh JSON payload against the committed artifacts.
