# 2026-04-16 interval-tree benchmark chart refresh

- Reused the existing benchmark-series CSV schema instead of inventing a second artifact format.
- SVG is enough for a portfolio chart here: readable in GitHub, diffable in reviews, and dependency-light compared with matplotlib.
- Parsing the CSV back into typed rows keeps the chart step resumable after a previous run already produced benchmark artifacts.
