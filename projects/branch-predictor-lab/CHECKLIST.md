# branch-predictor-lab checklist

## Completed slices
- [x] Implement always-taken and always-not-taken baselines
- [x] Implement one-bit and two-bit bimodal predictors with configurable table sizes
- [x] Implement a gshare predictor with XOR-based global-history indexing
- [x] Add a reusable local trace parser and a sample mixed-pattern trace
- [x] Add a compare/simulate CLI with text and JSON output modes
- [x] Add unit tests for parser, predictor behavior, ranking, and CLI output
- [x] Add portfolio-facing README notes, research notes, review logs, and wrap-up support
- [x] Add synthetic workload generators for loop-heavy, random-biased, and tournament-style traces
- [x] Add generator CLI coverage plus reproducibility checks for the new synthetic workloads
- [x] Add local-history, perceptron, and tournament predictors with advanced-predictor tests and JSON-visible state snapshots
- [x] Render Markdown/SVG predictor comparison cards for the docs artifact gallery
- [x] Add aliasing-focused traces and compare-output summaries so table-size trade-offs become easier to show in portfolio screenshots
- [x] Add a perceptron-majority synthetic workload and perceptron predictor follow-up for advanced architecture coverage
- [x] Add trace-family sweep commands that batch-generate workloads and compare predictors in one run
- [x] Add dynamic gshare-index collision summaries so history-dependent aliasing is visible alongside the static PC-index view
- [x] Add perceptron threshold/weight-limit sweep artifacts so neural tuning is visible in the gallery
- [x] Add budget-normalized sweeps so predictors can compete under similar state-bit budgets
- [x] Add CSV/export-friendly budget sweep output so README charts and slide decks can reuse the same winner matrix without re-parsing Markdown
- [x] Add side-by-side table-size sweep artifacts so static-PC and dynamic-gshare collision counts can be compared across the same workload family

## Next candidate slices
- [x] Add artifact-ready stacked bar / heatmap exports that summarize how often each predictor wins across the whole budget grid, not just per-workload rows
- [x] Add budget-grid runner-up stability or winner-margin trend artifacts so near-ties are visible alongside outright wins
- [x] Highlight budget crossover points where the winner changes so the artifact can call out the exact flip budgets
- [x] Annotate crossover-trigger cells directly on the winner matrix so slide screenshots show the exact flip location without reading the separate summary card
- [ ] Export a standalone crossover-only slide card (or PNG-friendly companion) when the full budget matrix is too dense for one screenshot
