# Review pass 1 - API contract

- Checked that plugin benchmark generation uses the same deterministic `(scenario, records, seed)` signature as the built-in benchmark path.
- Verified the plugin hook stays optional and does not change existing built-in or non-benchmark execution flows.
- Fix kept: `benchmark_records` is validated as callable during plugin load so failures happen early and read clearly.
