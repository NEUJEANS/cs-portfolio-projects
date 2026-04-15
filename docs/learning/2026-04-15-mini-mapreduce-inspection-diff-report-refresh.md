# Mini MapReduce inspection diff report refresh

- Markdown diff artifacts should keep a stable table layout so README/docs snapshots stay deterministic across runs.
- HTML artifacts can stay dependency-free by reusing inline tables and light CSS instead of adding a template engine.
- Self-test before coding: batch inspection should still support JSON-only and CSV-only flows while report outputs are optional side artifacts.
