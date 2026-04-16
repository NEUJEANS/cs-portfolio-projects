# mini-mapreduce plugin docs pages slice

- [x] confirm repo sync before editing
- [x] pick mini-mapreduce as the next unfinished project slice
- [x] skip external web research because the next step was already scoped locally in the project checklist
- [x] do a short Python `os.path.relpath` / slugged-filename refresh and self-test before coding
- [x] update/add checklist markdown so the slice is resumable
- [x] add dedicated per-plugin Markdown/HTML docs pages from `catalog-plugins --docs-dir`
- [x] make catalog quick-link landing cards point to the generated docs pages when `--docs-dir` is supplied
- [x] extend project-level and repo-level tests for plugin page generation and back-links to the catalog index
- [x] run project-level and repo-level mini-mapreduce tests
- [x] review pass 1: targeted unit/integration coverage for generated page paths and catalog links
- [x] review pass 2: `py_compile` for `mapreduce.py`, `projects/mini-mapreduce-lab/test_mapreduce.py`, and `tests/test_mini_mapreduce.py`
- [x] review pass 3: CLI smoke test for generated catalog + per-plugin Markdown/HTML docs pages
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] next: explore release-to-release comparison pages or docs-site sidebars once more bundled plugins exist
