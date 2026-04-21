# MinHash benchmark pack review log

## Pass 1, exact-pair ranking audit
- Issue found: benchmark summaries kept exact matches in pair-iteration order, so the medium scenario highlighted a weaker ETL pair instead of the strongest frontend pair.
- Fix: sort `top_exact_pairs` by exact score, estimated score, and shared bands before exporting benchmark payloads.

## Pass 2, CLI ergonomics audit
- Issue found: the new `write-benchmark-pack` positional argument had no descriptive help text, which made `--help` less clear for repeatable artifact generation.
- Fix: add destination help text describing that the command writes scenario folders plus benchmark summaries.

## Pass 3, summary readability audit
- Issue found: candidate-reduction values in the pack summary mixed raw float formatting (`1.0`) with four-decimal metrics elsewhere.
- Fix: render candidate-reduction ratios with four decimal places in the Markdown and HTML pack summaries.
