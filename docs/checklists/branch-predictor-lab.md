# branch-predictor-lab checklist

## Budget crossover highlight slice (2026-04-18 05:04 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around budget crossover points where the winning predictor changes
- [x] do a short Python adjacent-pair / crossover-summary refresh and self-test before coding
- [x] update checklist/docs so the slice is resumable
- [x] add workload-level and whole-grid budget crossover summaries so the exact budget transitions that flip winners are explicit
- [x] surface crossover points in Markdown/SVG/CSV budget-sweep artifacts and the JSON payload
- [x] extend tests for crossover summaries plus CLI export coverage
- [x] regenerate the committed budget-sweep artifacts and gallery copy
- [x] run targeted tests and 3 review passes
- [ ] run secret scan before push
- [ ] commit, push, and add wrap-up
- [ ] consider annotating crossover cells directly on the winner matrix or exporting slide-ready crossover-only cards in a future run

- [x] pick a computer-architecture project that broadens the portfolio beyond algorithms and systems tooling
- [x] note brief branch-prediction research takeaways before implementation
- [x] implement always-taken / always-not-taken baselines for comparison
- [x] implement one-bit and two-bit bimodal predictors with configurable table sizes
- [x] implement a gshare predictor with XOR-based global-history indexing
- [x] add a reusable text-trace parser and a sample mixed-pattern trace
- [x] add compare/simulate CLI flows with text and JSON output
- [x] add synthetic workload generation for loop-heavy, random-biased, and tournament-style traces
- [x] add tests for generator reproducibility, workload behavior, and CLI output
- [x] add local-history and tournament predictor coverage plus chooser-state inspection
- [x] add Markdown/SVG comparison-card export plus committed artifact-gallery assets
- [x] add alias-thrash synthetic workload and PC-index aliasing summaries for table-size trade-off demos
- [x] add a perceptron predictor plus a linearly separable long-history workload for stronger architecture coverage
- [x] add a trace-family sweep CLI plus committed Markdown/SVG overview artifacts
- [x] add dynamic gshare-index collision summaries so history-dependent aliasing is visible alongside the static PC-index view
- [x] log at least 3 review passes and fix issues found
- [x] list next candidate slices for advanced architecture follow-ups
- [x] add perceptron threshold/weight-limit sweep reports so the neural predictor has the same artifact depth as the alias-thrash demos
- [x] add budget-normalized sweeps so predictors can compete under similar state-bit budgets
- [x] add CSV/export-friendly budget winner matrices so README charts and slide decks can reuse the same sweep without re-parsing Markdown
- [ ] add side-by-side table-size sweep artifacts so static-PC and dynamic-gshare collision counts can be compared across the same workload family
