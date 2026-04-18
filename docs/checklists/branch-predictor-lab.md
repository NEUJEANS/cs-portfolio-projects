# branch-predictor-lab checklist

## Budget crossover slide-card slice (2026-04-18 08:41 UTC run)
- [x] confirm repo sync before editing
- [x] inspect the dirty local branch-predictor work instead of overwriting it with a different slice
- [x] finish the standalone crossover-only SVG card export and wire it through the CLI JSON/output paths
- [x] regenerate the committed budget-sweep artifact bundle with the new crossover card companion
- [x] update README/gallery/project checklist copy so the standalone card is documented and reproducible
- [x] run targeted tests plus a real budget-sweep smoke command with the new `--crossover-svg-out` flag
- [x] run at least 3 review passes and fix issues found
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [ ] consider HTML/PNG-friendly artifact companions in a future run

## Budget matrix crossover annotation slice (2026-04-18 05:35 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around annotating crossover cells directly on the winner matrix
- [x] do a short Python/SVG annotation refresh and self-test if implementation details need it
- [x] update checklist/docs so the slice is resumable before coding
- [x] annotate crossover-trigger budget cells directly on the budget-sweep winner matrix so slide screenshots show the flip location without reading the separate summary card
- [x] mirror the new matrix callouts in Markdown/README/gallery copy so the artifact story stays consistent
- [x] extend tests for SVG/Markdown annotation coverage and CLI export expectations
- [x] regenerate the committed budget-sweep artifacts after the annotation pass
- [x] run targeted tests and 3 review passes
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider exporting a standalone crossover-only slide card in a future run

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
- [x] run secret scan before push
- [x] commit, push, and add wrap-up
- [x] consider annotating crossover cells directly on the winner matrix or exporting slide-ready crossover-only cards in a future run

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
- [x] add side-by-side table-size sweep artifacts so static-PC and dynamic-gshare collision counts can be compared across the same workload family
