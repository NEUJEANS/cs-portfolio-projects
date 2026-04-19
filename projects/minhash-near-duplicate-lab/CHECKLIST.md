# minhash-near-duplicate-lab checklist

## Completed slices
- [x] Implement exact Jaccard, MinHash signatures, and LSH-style banding for near-duplicate detection
- [x] Add corpus scanning, pairwise comparison, and JSON/text CLI workflows
- [x] Add persisted signature indexes plus incremental refresh and dry-run diff support
- [x] Add benchmark export support for JSON, CSV, and Markdown summaries
- [x] Add curated preset corpora for mixed Markdown/code notebooks, data-science pipelines, and systems reconciliation stories
- [x] Add a frontend-focused `web-dev-component-clones` preset so the lab can demo near-duplicate React-style dashboard cards, hooks, notes, and styling files
- [x] Expand test coverage for preset generation and mixed-extension frontend corpus scans
- [x] Emit artifact-ready JSON/Markdown/HTML preset bundles next to generated preset corpora for easier portfolio screenshots
- [x] Harden preset bundle generation so reused destinations ignore stray files and notebook previews stay readable for both list- and string-based cell sources

## Next candidate slices
- [ ] Add richer benchmark dataset packs with expected-recall scenarios across tiny, medium, and noisy corpora
- [ ] Add language-aware literal buckets for lists, dicts, template strings, and JSX inline objects in code mode
- [ ] Add a cross-preset landing page that compares the mixed-language, data-science, systems, and web-dev demo bundles side by side
