# MinHash Near-Duplicate Lab Checklist

## Quality bar
- [x] core compare/corpus/index/benchmark workflows implemented
- [x] README explains usage, benchmarks, and interview talking points
- [x] repository tests cover API and CLI workflows
- [x] code-mode identifier normalization added
- [x] code-mode numeric literal normalization added
- [x] code-mode string/boolean/None/float literal normalization added
- [ ] mixed-language corpus presets for Markdown + code notebook demos
- [ ] dry-run corpus diff summary before refresh for very large indexes
- [ ] richer benchmark dataset pack with expected-recall scenarios

## This slice
- [x] upgrade code tokenization to preserve quoted strings and floating-point literals
- [x] normalize `True`/`False`, `None`, strings, floats, and integers into stable literal buckets
- [x] add regression tests for literal tokenization and similarity gains
- [x] refresh project README to document the broader literal normalization behavior
