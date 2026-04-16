# MinHash Near-Duplicate Lab Checklist

## Quality bar
- [x] core compare/corpus/index/benchmark workflows implemented
- [x] README explains usage, benchmarks, and interview talking points
- [x] repository tests cover API and CLI workflows
- [x] code-mode identifier normalization added
- [x] code-mode numeric literal normalization added
- [x] code-mode string/boolean/None/float literal normalization added
- [x] mixed-language corpus presets for Markdown + code notebook demos
- [ ] dry-run corpus diff summary before refresh for very large indexes
- [ ] richer benchmark dataset pack with expected-recall scenarios

## This slice
- [x] add a curated `mixed-markdown-code-notebook` preset with Markdown, Python, and notebook files
- [x] support comma-separated glob patterns so mixed-language corpora can be scanned and indexed in one run
- [x] add regression tests for preset generation and mixed-glob corpus scans
- [x] refresh project README to document the new preset workflow and mixed-language demo usage
