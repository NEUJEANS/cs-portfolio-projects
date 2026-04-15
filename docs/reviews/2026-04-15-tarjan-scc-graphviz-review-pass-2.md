# Tarjan SCC Graphviz review pass 2

- Focus: automated and CLI smoke coverage.
- Check: ran `./.venv/bin/python -m pytest -q projects/tarjan-scc-lab/test_tarjan_scc_lab.py` and a direct `dot` CLI smoke run.
- Fix made: corrected the CLI output assertion to match literal `\\n` escapes in DOT labels.
