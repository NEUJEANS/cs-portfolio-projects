# Review pass 2 — mini-mapreduce plugin metadata diff slice

- audited README, checklist, and learning-note consistency for the new inspection diff workflow
- issue found: the docs needed an explicit example showing that diffs live in the JSON payload while CSV remains the stable snapshot export
- fix applied: added a dedicated `inspect-plugin --diff` usage example and updated the feature/future-improvements notes accordingly
