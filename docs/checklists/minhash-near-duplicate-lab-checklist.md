# MinHash Near-Duplicate Lab Checklist

## Quality bar
- [x] core compare/corpus/index/benchmark workflows implemented
- [x] README explains usage, benchmarks, and interview talking points
- [x] repository tests cover API and CLI workflows
- [x] code-mode identifier normalization added
- [x] code-mode numeric literal normalization added
- [x] code-mode string/boolean/None/float literal normalization added
- [x] mixed-language corpus presets for Markdown + code notebook demos
- [x] richer preset families for data-science and systems-programming style clone-detection demos
- [x] dry-run corpus diff summary before refresh for very large indexes
- [x] richer benchmark dataset pack with expected-recall scenarios

## This slice
- [x] add a committed `write-benchmark-pack` workflow for tiny, medium, and noisy corpora
- [x] record expected recall ranges and observed benchmark results for each scenario
- [x] export pack-level JSON, CSV, Markdown, and HTML artifacts that are easy to reuse in a portfolio
- [x] add regression tests covering the benchmark-pack writer and CLI flow
