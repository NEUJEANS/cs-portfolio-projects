# minhash-near-duplicate-lab checklist

## Initial slice (2026-04-14 21:19 UTC run)
- [x] confirm repo sync before editing
- [x] do brief research on shingling, MinHash, Jaccard similarity, and banding
- [x] refresh Python standard-library implementation patterns and self-test the planned API shape
- [x] create a new portfolio-worthy project for near-duplicate text detection
- [x] implement exact comparison plus approximate MinHash/LSH-style corpus scanning
- [x] add README usage, interview talking points, and future improvements
- [x] add repository-level automated tests for API behavior and CLI flows
- [x] complete at least 3 review passes and log fixes

## Persistence + benchmark slice (2026-04-14 22:33 UTC run)
- [x] confirm repo sync before editing
- [x] review prior roadmap and choose the unfinished persistence/benchmark follow-up
- [x] do a quick Python refresh/self-test against the current MinHash API before editing
- [x] add persistent signature index support with metadata and reusable stored signatures
- [x] add CLI commands for `build-index` and `scan-index`
- [x] add a benchmark command comparing LSH candidate generation with exact all-pairs scanning
- [x] expand tests for index round-trips and new CLI flows
- [x] update README with new usage examples and interview talking points
- [x] complete at least 3 review passes and fix issues found

## Incremental refresh slice (2026-04-15 05:29 UTC run)
- [x] confirm repo sync before editing
- [x] choose the next unfinished MinHash follow-up around incremental index refresh
- [x] do a quick Python refresh/self-test around dataclass reuse and content-hash based change detection
- [x] implement `refresh-index` so unchanged documents reuse stored signatures while changed/new files are recomputed
- [x] keep refresh resumable by preserving index metadata and safely dropping removed files on rebuild
- [x] expand tests for refresh stats, reused signatures, and CLI refresh JSON output
- [x] update README usage and talking points for repeated corpus rescans
- [x] complete at least 3 review passes and fix issues found
## Benchmark export slice (2026-04-15 05:39 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued benchmark-export follow-up from the MinHash checklist
- [x] refresh Python file-output patterns and benchmark summary payload design
- [x] add benchmark report export support for JSON, CSV, and Markdown summaries
- [x] expose CLI output-path support and keep the command resumable for repeated corpus runs
- [x] expand tests for export helpers and benchmark CLI file generation
- [x] update README usage and interview framing for portfolio write-ups
- [x] complete at least 3 review passes and fix issues found

## Token-mode expansion slice (2026-04-15 20:02 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around code-oriented and character-level dedup modes
- [x] do brief research on token shingles vs character shingles for near-duplicate and code-clone style scans
- [x] refresh Python tokenizer/shingling patterns and self-test the planned mode API
- [x] add `word`, `code`, and `char` token modes while keeping `word` as the default
- [x] persist token-mode metadata in saved signature indexes so refresh/scan stay resumable
- [x] expand tests for tokenizer modes, CLI mode flags, benchmark export metadata, and index round-trips
- [x] update README usage, feature notes, and future roadmap
- [x] complete at least 3 review passes and fix issues found

## Identifier-normalization slice (2026-04-15 20:39 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around code-mode identifier normalization
- [x] do a quick tokenizer/keyword refresh and self-test the planned normalization rules
- [x] add `--normalize-identifiers` support for `compare`, `corpus`, `build-index`, and `benchmark` in `code` mode
- [x] persist normalization metadata in saved signature indexes so refresh/scan stay resumable
- [x] expand tests for normalized tokenization, similarity changes, CLI validation, benchmark exports, and index round-trips
- [x] update README usage, feature notes, and future roadmap
- [x] complete at least 3 review passes and fix issues found

## Literal-normalization slice (2026-04-15 20:42 UTC run)
- [x] confirm repo sync before editing
- [x] choose the queued follow-up around code-mode literal normalization
- [x] do a quick tokenizer refresh and self-test for number-token bucketing rules
- [x] add `--normalize-literals` support for `compare`, `corpus`, `build-index`, and `benchmark` in `code` mode
- [x] persist literal-normalization metadata in saved signature indexes so refresh/scan stay resumable
- [x] expand tests for normalized tokenization, similarity changes, CLI validation, benchmark exports, and index round-trips
- [x] update README usage, feature notes, and future roadmap
- [x] complete at least 3 review passes and fix issues found

## Dry-run refresh summary slice (2026-04-16 01:51 UTC run)
- [x] confirm repo sync before editing
- [x] choose the remaining MinHash follow-up around dry-run refresh previews for large indexes
- [x] do a quick Python refresh/self-test around path-diff summaries and non-mutating CLI flows
- [x] add `refresh-index --dry-run` so saved indexes can preview reused/updated/added/removed files before rewrite
- [x] keep refresh resumable by exposing path-level summaries while leaving the index untouched in dry-run mode
- [x] expand tests for summary helpers and dry-run CLI JSON output
- [x] update README usage, feature notes, and interview framing
- [x] complete at least 3 review passes and fix issues found

## Cross-preset landing page slice (2026-04-19 16:41 UTC run)
- [x] confirm repo sync before editing
- [x] resume the queued MinHash follow-up around a cross-preset landing page
- [x] skip external research because the slice stays inside the existing preset bundle/export architecture
- [x] self-test the planned bundle-summary aggregation path with new repo-level unit and CLI coverage
- [x] add `write-preset-landing` so checked-in bundle summaries can produce a shared Markdown/HTML comparison page
- [x] generate and check in bundle artifacts for the mixed-markdown, data-science, systems, and web-dev presets
- [x] update README usage, interview framing, and future-follow-up notes
- [x] complete at least 3 review passes and fix issues found
