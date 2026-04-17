# Mini MapReduce docs index review — 2026-04-17

## Pass 1 — docs/index content audit
- found ambiguous Markdown browser-link labels for annotation-batch presets because both links rendered as `Annotation batch HTML — …` without the preset name
- fixed the label format to include `/ {preset.name}` so `full` and `portfolio-tight` are distinguishable
- fixed project docs drift: the project checklist still showed batch presets as unfinished and the README still listed the docs index as a future improvement

## Pass 2 — artifact generation audit
- generated a real committed artifact bundle under `docs/artifacts/mini-mapreduce/` covering:
  - plugin catalog (`plugin-catalog.*`)
  - dedicated plugin pages (`plugin-pages/*`)
  - plugin comparison diff (`plugin-comparison-diff.*`)
  - project-week benchmark bundle (`2026-04-17-project-week-*`)
  - docs index (`docs-index.md`, `docs-index.html`, `docs-index.json`)
- caught accidental timing-only churn in the older annotation-batch benchmark artifacts after a regeneration run
- restored the pre-existing annotation-batch artifacts from `HEAD` so this slice adds only the new docs-index-related bundle

## Pass 3 — runnable + link audit
- reran:
  - `python3 -m py_compile projects/mini-mapreduce-lab/mapreduce.py projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
  - `python3 -m unittest projects/mini-mapreduce-lab/test_mapreduce.py tests/test_mini_mapreduce.py`
- ran a link audit that checks:
  - every file referenced by `docs/artifacts/mini-mapreduce/docs-index.json` exists
  - the README links to `docs-index.md` and `docs-index.html` resolve correctly from `projects/mini-mapreduce-lab/README.md`
- result: all checks passed
