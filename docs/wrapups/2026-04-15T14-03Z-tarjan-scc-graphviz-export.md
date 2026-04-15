# Tarjan SCC Graphviz export wrap-up

- Timestamp: 2026-04-15 14:03 UTC
- Project: `tarjan-scc-lab`
- What changed:
  - added a `dot` CLI mode that exports the condensation DAG as Graphviz DOT
  - labeled SCC nodes with topology level and size for cleaner portfolio screenshots
  - documented DOT rendering in the project README and added DOT-focused tests/review notes
- Tests run:
  - `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py`
  - `./.venv/bin/python projects/tarjan-scc-lab/tarjan_scc_lab.py projects/tarjan-scc-lab/sample_graph.json dot | sed -n '1,12p'`
- Reviews run:
  - `docs/reviews/2026-04-15-tarjan-scc-graphviz-review-pass-1.md`
  - `docs/reviews/2026-04-15-tarjan-scc-graphviz-review-pass-2.md`
  - `docs/reviews/2026-04-15-tarjan-scc-graphviz-review-pass-3.md`
- Secret scan:
  - `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- Commit: `f7b28369d0ba4a3b95c0e4f69ae2e3fb707b96cd`
- Next step: add Mermaid export support so the condensation DAG can be embedded directly in markdown docs and GitHub views.
