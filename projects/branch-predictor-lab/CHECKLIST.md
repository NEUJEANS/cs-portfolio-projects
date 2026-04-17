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

## Next candidate slices
- [ ] Add trace-family sweep commands that batch-generate workloads and compare predictors in one run
- [ ] Add perceptron threshold/weight-limit sweep artifacts so neural tuning is visible in the gallery
- [ ] Add dynamic gshare-index collision summaries so history-dependent aliasing is visible alongside the static PC-index view
