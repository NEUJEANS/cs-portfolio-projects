# CRDT OR-Set Lab — preset bundle landing + ZIP research (2026-04-18)

## Goal
Make each `compare-presets --detail-output-dir ...` preset directory more portable so one preset can be shared and understood without needing the whole repo tree open beside it.

## Brief reference checked
- Python `zipfile` docs: `ZipFile(..., mode="w", compression=ZIP_DEFLATED)` is the standard-library path for creating a normal ZIP archive without adding third-party dependencies.

## Notes pulled into the implementation
- Keep the bundle self-contained by copying the scenario script into the preset directory instead of linking the HTML pages back out to `projects/crdt-orset-lab/...`.
- Generate a tiny `index.html` landing page inside each preset directory so reviewers have one obvious entry point instead of several sibling HTML files with no bundle-level summary.
- Build the ZIP packet only from files already inside the bundle directory so the archive stays portable and does not accidentally depend on repo-relative parent paths.
- Prefer a fixed file list/order for the ZIP packet so tests can assert the archive contents deterministically.

## Scope chosen
- add bundled `scenario-script.json` copies inside each preset detail directory
- add per-preset `index.html` landing pages that summarize the scenario and link every companion artifact
- add one ZIP packet per preset bundle
- surface bundle + ZIP links from the suite Markdown/HTML/JSON outputs

## Deferred
- batch download / multi-preset packaging from the suite page
- PNG exports layered on top of the existing SVG replay checkpoint downloads
- broader CRDT-family comparison pages beyond OR-Set vs LWW
