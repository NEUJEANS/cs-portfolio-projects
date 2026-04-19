# log-analyzer review — 2026-04-19 — facet detail bundles

## Pass 1 — code-path / regression review
- Re-read the new `build_facet_ranking_groups()` reuse path plus the CLI wiring in `main()` to make sure the new bundle export stayed on top of the existing facet-ranking pipeline instead of forking a second analysis path.
- Issue found: rerunning the bundle into the same output directory could leave stale `slices/*.html` files behind when a later run produced fewer facet slices, which would make the committed artifact directory drift from the manifest/ZIP packet.
- Fix: clear previously generated `slices/*.html` files before writing the current run so the output directory, manifest, and ZIP stay aligned.

## Pass 2 — artifact smoke review
- Regenerated the committed sample bundle with `--facet-ranking-detail-bundle-dir docs/artifacts/log-analyzer/facet-ranking-detail-bundle` alongside the existing gallery export.
- Verified `index.html`, `manifest.json`, and the per-slice HTML pages were created, and checked that gallery back-links / related-link rewrites resolve relative to the bundle directory structure.
- Ran a local manifest/ZIP validation script to confirm every listed slice file exists, every gallery focus link is embedded in the corresponding slice page, ZIP members are ordered as expected, and all archive entries use the fixed timestamp for deterministic reruns.
- Browser automation was unavailable during this pass, so the artifact validation used file/link checks rather than a browser snapshot; no functional issues remained after the stale-slice cleanup.

## Pass 3 — docs / resumability audit
- Re-read `projects/log-analyzer/README.md`, `projects/log-analyzer/CHECKLIST.md`, `docs/checklists/log-analyzer.md`, the new research note, and the refresh/self-test note.
- Confirmed the new flag, workflow examples, committed artifact path, and next-step ideas all point to the detail-bundle slice instead of the already-finished gallery deep-link work.
- No additional issues found.

## Final verification
- `python3 -m py_compile projects/log-analyzer/log_analyzer.py`
- `python3 -m unittest discover -s projects/log-analyzer -p 'test_*.py'`
- bundle/export smoke:
  - `python3 projects/log-analyzer/log_analyzer.py docs/artifacts/log-analyzer/facet-ranking-sample.log --facet-field env --facet-field region --top 3 --top-ip-facet-csv docs/artifacts/log-analyzer/top-ips-by-facet.csv --top-path-facet-csv docs/artifacts/log-analyzer/top-paths-by-facet.csv --top-referrer-facet-csv docs/artifacts/log-analyzer/top-referrers-by-facet.csv --top-user-agent-facet-csv docs/artifacts/log-analyzer/top-user-agents-by-facet.csv --facet-ranking-gallery-link 'Comparison card HTML=docs/artifacts/log-analyzer/release-comparison-card.html' --facet-ranking-gallery-link 'Annotated comparison card HTML=docs/artifacts/log-analyzer/release-comparison-card-annotated.html' --facet-ranking-gallery-link 'Top IPs CSV=docs/artifacts/log-analyzer/top-ips-by-facet.csv' --facet-ranking-gallery-link 'Top paths CSV=docs/artifacts/log-analyzer/top-paths-by-facet.csv' --facet-ranking-gallery-link 'Top referrers CSV=docs/artifacts/log-analyzer/top-referrers-by-facet.csv' --facet-ranking-gallery-link 'Top user agents CSV=docs/artifacts/log-analyzer/top-user-agents-by-facet.csv' --facet-ranking-gallery-html docs/artifacts/log-analyzer/facet-ranking-gallery.html --facet-ranking-detail-bundle-dir docs/artifacts/log-analyzer/facet-ranking-detail-bundle`
  - `python3 - <<'PY'
import json, zipfile
from pathlib import Path
bundle_dir = Path('docs/artifacts/log-analyzer/facet-ranking-detail-bundle')
manifest = json.loads((bundle_dir / 'manifest.json').read_text(encoding='utf-8'))
assert (bundle_dir / 'index.html').exists()
assert (bundle_dir / manifest['bundle_files']['bundle_zip']).exists()
for slice_entry in manifest['slices']:
    slice_path = bundle_dir / slice_entry['detail_html']
    assert slice_path.exists(), slice_path
    html = slice_path.read_text(encoding='utf-8')
    assert slice_entry['card_id'] in html
    assert slice_entry['gallery_focus_href'] in html
with zipfile.ZipFile(bundle_dir / manifest['bundle_files']['bundle_zip']) as archive:
    names = archive.namelist()
    expected = ['index.html', 'manifest.json', *sorted(slice['detail_html'] for slice in manifest['slices'])]
    assert names == expected, (names, expected)
    assert all(info.date_time == (2020, 1, 1, 0, 0, 0) for info in archive.infolist())
print('bundle-manifest-link-check: OK')
PY`
- `git diff --check`