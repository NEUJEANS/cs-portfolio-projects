# MinHash Near-Duplicate Lab Checklist

## Quality bar
- [x] core compare/corpus/index/benchmark workflows implemented
- [x] README explains usage, benchmarks, and interview talking points
- [x] repository tests cover API and CLI workflows
- [x] code-mode identifier normalization added
- [x] code-mode numeric literal normalization added
- [x] code-mode string/boolean/None/float literal normalization added
- [x] mixed-language corpus presets for Markdown + code notebook demos
- [x] dry-run corpus diff summary before refresh for very large indexes
- [ ] richer benchmark dataset pack with expected-recall scenarios

## This slice
- [x] add `refresh-index --dry-run` to preview reused, updated, added, and removed files before rewriting the index
- [x] expose path-level dry-run summaries in JSON and readable CLI output for resumable large-corpus maintenance
- [x] add regression tests covering summary helpers and dry-run CLI behavior without mutating the saved index
- [x] refresh project README to document the dry-run refresh workflow and interview framing
